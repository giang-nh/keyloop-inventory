"""Three years of simulated dealership data. The rules are in docs/DATA_SIMULATION.md.

The model mix, prices, launch dates and Lunar New Year dates come from public Vietnamese
market data (sources in the document). Selling times and the effect of actions are
assumptions: there is no public data on how long cars stay in stock at Vietnamese dealers.

Everything comes from one random seed, so the same seed and reference date always give
the same data.
"""

import math
import random
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models import ActionType, Dealership, Vehicle, VehicleAction
from app.services.aging import AGING_AFTER_DAYS, APPROACHING_FROM_DAYS
from app.services.loading import VehicleRecord, check_records

YEARS = 3
WARM_UP_DAYS = 182
YEARLY_GROWTH = 0.05

# name, city, average new cars per day, managers
DEALERSHIPS = [
    ("Riverside Motors", "Ho Chi Minh City", 3.0, ("An Nguyen", "Linh Tran")),
    ("Lakeside Cars", "Hanoi", 2.2, ("Minh Pham", "Hoa Le")),
    ("Harbour Auto", "Da Nang", 1.6, ("Quang Vo", "Thu Dang")),
    ("Hilltop Autos", "Can Tho", 1.0, ("Bao Huynh", "Mai Do")),
]

MILLION = 1_000_000

# The 14 models with the highest 2025 sales in Vietnam that have a public price list.
# make, model, units sold in 2025 (sets the share of arrivals), lowest and highest list
# price in VND (September 2026), first month on sale (None = on sale for the whole period).
CATALOG = [
    ("VinFast", "VF 3", 44_585, 299 * MILLION, 299 * MILLION, date(2024, 8, 1)),
    ("VinFast", "VF 5", 43_913, 529 * MILLION, 529 * MILLION, None),
    ("VinFast", "Limo Green", 27_127, 699 * MILLION, 699 * MILLION, date(2025, 9, 1)),
    ("VinFast", "VF 6", 23_291, 646 * MILLION, 699 * MILLION, None),
    ("Mitsubishi", "Xpander", 19_891, 555 * MILLION, 688 * MILLION, None),
    ("Ford", "Ranger", 18_692, 659 * MILLION, 1_202 * MILLION, None),
    ("Mazda", "CX-5", 17_262, 694 * MILLION, 979 * MILLION, None),
    ("Mitsubishi", "Xforce", 15_254, 605 * MILLION, 720 * MILLION, None),
    ("Toyota", "Yaris Cross", 14_601, 730 * MILLION, 838 * MILLION, None),
    ("Toyota", "Vios", 13_424, 458 * MILLION, 545 * MILLION, None),
    ("Honda", "City", 10_899, 499 * MILLION, 599 * MILLION, None),
    ("Hyundai", "Tucson", 9_243, 769 * MILLION, 989 * MILLION, None),
    ("Kia", "Seltos", 6_577, 599 * MILLION, 799 * MILLION, None),
    ("Suzuki", "XL7 Hybrid", 2_633, 599_900_000, 607_900_000, None),
]

# First day of the Lunar New Year (Tet). Car sales in Vietnam drop sharply around it:
# January 2025, the Tet month, was down 40% on December (VietnamPlus).
TET = {
    2023: date(2023, 1, 22),
    2024: date(2024, 2, 10),
    2025: date(2025, 1, 29),
    2026: date(2026, 2, 17),
    2027: date(2027, 2, 6),
}
TET_SLOWDOWN = (-7, 7)  # days around Tet when arrivals drop and sales pause
TET_ARRIVAL_FACTOR = 0.4

# More arrivals in the last quarter, when dealers stock up for year-end sales.
MONTH_FACTOR = [1.0, 1.0, 1.0, 1.0, 1.0, 0.95, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]

TYPICAL_DAYS_TO_SELL = 38
DAYS_TO_SELL_SPREAD = 0.8  # log-normal sigma: a long tail of slow sellers

# Assumed effect of an action on the remaining time to sell (1.0 = no effect).
ACTION_EFFECT = {
    ActionType.PRICE_REDUCTION_PLANNED: 0.5,
    ActionType.MARKETING_PROMOTION: 0.7,
    ActionType.TRANSFER_TO_ANOTHER_DEALERSHIP: 0.8,
    ActionType.UNDER_REVIEW: 1.0,
    ActionType.OTHER: 1.0,
}
MAIN_ACTION_CHOICES = [
    (ActionType.PRICE_REDUCTION_PLANNED, 45),
    (ActionType.MARKETING_PROMOTION, 25),
    (ActionType.TRANSFER_TO_ANOTHER_DEALERSHIP, 15),
    (ActionType.OTHER, 10),
    (ActionType.UNDER_REVIEW, 5),
]
NOTES = {
    ActionType.PRICE_REDUCTION_PLANNED: ["Reduce by 3%", "Reduce by 5%", "Match nearby dealer"],
    ActionType.MARKETING_PROMOTION: ["Weekend campaign", "Feature on website", "Social media"],
    ActionType.TRANSFER_TO_ANOTHER_DEALERSHIP: ["Better demand in another city"],
    ActionType.SEND_TO_AUCTION: ["No interest after price cut", None],
    ActionType.UNDER_REVIEW: [None, "Check pricing against market"],
    ActionType.OTHER: ["Offer free service package", None],
}

TRADE_IN_SHARE = 0.02
MISSING_DATE_SHARE = 0.01  # of cars in stock without actions
_VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"  # VINs never use I, O or Q


@dataclass
class SimAction:
    action_type: ActionType
    created_by: str
    created_at: datetime
    note: str | None


@dataclass
class SimVehicle:
    dealership: int  # position in DEALERSHIPS
    record: VehicleRecord
    actions: list[SimAction] = field(default_factory=list)
    model_index: int = -1  # position in CATALOG, so a trade-in comes back as the same model


@dataclass
class Dataset:
    reference_date: date
    dealerships: list[tuple[str, str]]
    vehicles: list[SimVehicle]


class _Simulator:
    def __init__(self, seed: int, reference_date: date):
        self.rng = random.Random(seed)
        self.reference_date = reference_date
        self.window_start = reference_date - timedelta(days=round(YEARS * 365.25))
        self.start = self.window_start - timedelta(days=WARM_UP_DAYS)
        self.weights = [c[2] for c in CATALOG]

    def vin(self) -> str:
        return "".join(self.rng.choice(_VIN_CHARS) for _ in range(17))

    @staticmethod
    def near_tet(day: date) -> bool:
        tet = TET.get(day.year)
        before, after = TET_SLOWDOWN
        return tet is not None and before <= (day - tet).days <= after

    def arrivals_today(self, day: date, per_day: float) -> int:
        years_in = (day - self.start).days / 365.25
        expected = per_day * MONTH_FACTOR[day.month - 1] * (1 + YEARLY_GROWTH) ** years_in
        if self.near_tet(day):
            expected *= TET_ARRIVAL_FACTOR
        # Poisson draw (Knuth's method), fine for small averages.
        limit, count, product = math.exp(-expected), 0, self.rng.random()
        while product > limit:
            count += 1
            product *= self.rng.random()
        return count

    def days_to_sell(self) -> int:
        # No public data by model, so every model shares one assumed distribution.
        return max(
            1, round(self.rng.lognormvariate(math.log(TYPICAL_DAYS_TO_SELL), DAYS_TO_SELL_SPREAD))
        )

    def after_tet(self, arrived: date, days: int) -> int:
        """Sales pause around Tet: a sale that would fall then happens after it."""
        sale = arrived + timedelta(days=days)
        if self.near_tet(sale):
            resume = TET[sale.year] + timedelta(days=TET_SLOWDOWN[1] + 1 + self.rng.randint(0, 10))
            return (resume - arrived).days
        return days

    def pick_model(self, day: date) -> int:
        on_sale = [i for i, c in enumerate(CATALOG) if c[5] is None or c[5] <= day]
        return self.rng.choices(on_sale, [self.weights[i] for i in on_sale])[0]

    def stamp(self, day: date) -> datetime:
        # Office hours in Vietnam (08:00 to 18:00, UTC+7) are 01:00 to 11:00 UTC.
        return datetime.combine(day, time(self.rng.randint(1, 10), self.rng.randint(0, 59)), UTC)

    def act(self, arrived: date, days_to_sell: int, managers) -> tuple[int, list[SimAction]]:
        """Actions while the car is unsold, and the (possibly shorter) time to sell."""
        actions = []

        def record(on_day: int, action_type: ActionType) -> bool:
            when = arrived + timedelta(days=on_day)
            if on_day >= days_to_sell or when > self.reference_date:
                return False
            actions.append(
                SimAction(action_type, self.rng.choice(managers), self.stamp(when),
                          self.rng.choice(NOTES[action_type]))
            )
            return True

        if self.rng.random() < 0.5:
            record(self.rng.randint(APPROACHING_FROM_DAYS, 85), ActionType.UNDER_REVIEW)

        main_day = self.rng.randint(AGING_AFTER_DAYS + 1, 100)
        choice = self.rng.choices(*zip(*MAIN_ACTION_CHOICES, strict=True))[0]
        if self.rng.random() < 0.85 and record(main_day, choice):
            remaining = days_to_sell - main_day
            days_to_sell = main_day + max(1, round(remaining * ACTION_EFFECT[choice]))

        auction_day = self.rng.randint(150, 170)
        if self.rng.random() < 0.6 and record(auction_day, ActionType.SEND_TO_AUCTION):
            days_to_sell = min(days_to_sell, auction_day + self.rng.randint(7, 21))

        return days_to_sell, actions

    def car(self, dealership: int, arrived: date, vin: str | None = None,
            model_index: int | None = None, price: int | None = None,
            model_year: int | None = None) -> SimVehicle:
        if model_index is None:
            model_index = self.pick_model(arrived)
        make, model, _, lowest, highest, launched = CATALOG[model_index]
        if price is None:
            # A version somewhere in the model's price list, to the nearest million.
            price = lowest
            if highest > lowest:
                # Round to the nearest million, but never outside the price list.
                price = min(highest, max(lowest, int(round(self.rng.uniform(lowest, highest), -6))))
        if model_year is None:
            new_model = launched is not None and launched.year == arrived.year
            recent = new_model or self.rng.random() < 0.7
            model_year = arrived.year if recent else arrived.year - 1

        days, actions = self.act(
            arrived, self.after_tet(arrived, self.days_to_sell()), DEALERSHIPS[dealership][3]
        )
        sold = arrived + timedelta(days=days)
        record = VehicleRecord(
            vin=vin or self.vin(),
            make=make,
            model=model,
            model_year=model_year,
            price=price,
            stock_in_date=arrived,
            sold_date=sold if sold <= self.reference_date else None,
        )
        return SimVehicle(dealership, record, actions, model_index)

    def run(self) -> Dataset:
        vehicles: list[SimVehicle] = []
        day = self.start
        while day <= self.reference_date:
            for index, (_, _, per_day, _) in enumerate(DEALERSHIPS):
                for _ in range(self.arrivals_today(day, per_day)):
                    vehicles.append(self.car(index, day))
            day += timedelta(days=1)

        vehicles += self.trade_ins(vehicles)
        # Keep only cars still in stock when the three years begin, or arriving after.
        vehicles = [
            v for v in vehicles
            if v.record.sold_date is None or v.record.sold_date >= self.window_start
        ]
        vehicles = self.blank_some_dates(vehicles)
        vehicles.sort(key=lambda v: (v.record.stock_in_date or self.reference_date, v.record.vin))
        return Dataset(
            self.reference_date, [(name, city) for name, city, _, _ in DEALERSHIPS], vehicles
        )

    def trade_ins(self, vehicles: list[SimVehicle]) -> list[SimVehicle]:
        returns = []
        for original in vehicles:
            sold = original.record.sold_date
            if sold is None or self.rng.random() >= TRADE_IN_SHARE:
                continue
            back = sold + timedelta(days=self.rng.randint(200, 700))
            if back > self.reference_date:
                continue
            returns.append(
                self.car(
                    original.dealership, back, vin=original.record.vin,
                    model_index=original.model_index,
                    price=int(round(original.record.price * self.rng.uniform(0.6, 0.75), -6)),
                    model_year=original.record.model_year,
                )
            )
        return returns

    def blank_some_dates(self, vehicles: list[SimVehicle]) -> list[SimVehicle]:
        result = []
        for v in vehicles:
            in_stock_without_actions = v.record.sold_date is None and not v.actions
            if in_stock_without_actions and self.rng.random() < MISSING_DATE_SHARE:
                v = SimVehicle(v.dealership, replace(v.record, stock_in_date=None), [],
                               v.model_index)
            result.append(v)
        return result


def generate(reference_date: date, seed: int = 42) -> Dataset:
    """Build the dataset. Same seed and reference date, same data."""
    return _Simulator(seed, reference_date).run()


def load(session: Session, dataset: Dataset) -> None:
    """Check every record with the normal loader rules, then save everything at once."""
    check_records([v.record for v in dataset.vehicles], dataset.reference_date)

    dealerships = [Dealership(name=name, city=city) for name, city in dataset.dealerships]
    session.add_all(dealerships)
    for sim in dataset.vehicles:
        r = sim.record
        vehicle = Vehicle(
            vin=r.vin, dealership=dealerships[sim.dealership], make=r.make, model=r.model,
            model_year=r.model_year, price=r.price, stock_in_date=r.stock_in_date,
            sold_date=r.sold_date,
        )
        vehicle.actions = [
            VehicleAction(action_type=a.action_type, created_by=a.created_by,
                          created_at=a.created_at, note=a.note)
            for a in sim.actions
        ]
        session.add(vehicle)
    session.commit()
