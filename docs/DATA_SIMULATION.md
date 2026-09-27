# Data Simulation Rules

This document explains how `scripts/generate_data.py` builds three years of sample
dealership data for the API demo and the Power BI dashboard.

> **Status: proposed by the AI, waiting for the owner's approval (issue #25).**

## Why simulated data

There is no real dealership data in this assessment. A handful of hand-made records can
test the rules, but cannot show trends. Three years of simulated data lets the dashboard
answer the manager's fourth question, *"Is it getting better or worse?"*

## What is real, and what is assumed

We looked for a public dataset of dealer stock in Vietnam: which cars were in stock, for
how long, and when they sold. **There is none.** Market reports with this detail are paid
and not public. Used-car listing sites exist, but listings are not dealer stock, and
copying them would break their terms of use.

So the data mixes public market facts with assumptions. Each rule below is marked:

| Mark | Meaning |
|---|---|
| 📊 **Public data** | Taken from a public source, listed at the end |
| 🔧 **Assumption** | Our choice, because no public data exists |

## ⚠️ Read this before drawing conclusions from the dashboard

**The selling times and the effect of actions are assumptions.** In particular, the rules
*assume* that a price reduction or a promotion helps a car sell sooner. So when the
dashboard shows that actions help, it is showing our assumption, not evidence.

The data is good for showing that the service and the dashboard work, with a realistic
Vietnamese model mix, prices and seasons. It says nothing about how real dealerships
perform.

## The rules

Everything is driven by one random seed (default 42). The same seed and the same
reference date always give exactly the same data.

### Time span

- The data covers the **three years up to the reference date** (default: today, UTC).
- The simulation starts six months earlier and keeps only the cars still in stock when
  the three years begin. So the first month already has a normal amount of stock, instead
  of starting from an empty lot.

### Dealerships 🔧

| Dealership | City | New cars per day (average) | Managers |
|---|---|---|---|
| Riverside Motors | Ho Chi Minh City | 3.0 | An Nguyen, Linh Tran |
| Lakeside Cars | Hanoi | 2.2 | Minh Pham, Hoa Le |
| Harbour Auto | Da Nang | 1.6 | Quang Vo, Thu Dang |
| Hilltop Autos | Can Tho | 1.0 | Bao Huynh, Mai Do |

All names are made up. Each dealership sells every brand in the catalog. In Vietnam most
dealerships sell a single brand, and VinFast sells mainly through its own network; a
multi-brand group keeps the demo simple.

### Cars: model mix and prices 📊

The catalog holds the **14 best-selling models of 2025** in Vietnam that have a public
price list. A model's share of arrivals follows its 2025 sales. Each car gets a price
somewhere in its model's list-price range, rounded to the nearest million VND and never
outside the range.

| Make | Model | Units sold in 2025 | List price (VND, Sept 2026) | On sale from |
|---|---|---:|---|---|
| VinFast | VF 3 | 44,585 | 299 million | Aug 2024 |
| VinFast | VF 5 | 43,913 | 529 million | whole period |
| VinFast | Limo Green | 27,127 | 699 million | Sept 2025 |
| VinFast | VF 6 | 23,291 | 646–699 million | whole period |
| Mitsubishi | Xpander | 19,891 | 555–688 million | whole period |
| Ford | Ranger | 18,692 | 659 million – 1.202 billion | whole period |
| Mazda | CX-5 | 17,262 | 694–979 million | whole period |
| Mitsubishi | Xforce | 15,254 | 605–720 million | whole period |
| Toyota | Yaris Cross | 14,601 | 730–838 million | whole period |
| Toyota | Vios | 13,424 | 458–545 million | whole period |
| Honda | City | 10,899 | 499–599 million | whole period |
| Hyundai | Tucson | 9,243 | 769–989 million | whole period |
| Kia | Seltos | 6,577 | 599–799 million | whole period |
| Suzuki | XL7 Hybrid | 2,633 | 599.9–607.9 million | whole period |

Prices are in VND (SPEC D-10). Two simplifications:

- **Today's prices are used for all three years.** Price changes over time are not modelled.
- **Launch dates are used for VF 3 and Limo Green only**, where a public source gives them.
  The other models are treated as on sale for the whole period.

**Known skew:** VinFast makes up about **45%** of the cars in the data, against a **29%**
share of the whole 2025 market. Its models top the best-seller list, while the smaller
models of other brands are not in the catalog.

### Arrivals

- 🔧 Each day, each dealership receives a random number of cars around its average.
- 📊 **Lunar New Year (Tet):** car sales in Vietnam drop sharply around Tet. In January
  2025, the Tet month, sales fell 40% compared with December. The data uses the real
  date of Tet each year (22 Jan 2023, 10 Feb 2024, 29 Jan 2025, 17 Feb 2026). For a week
  either side of Tet, arrivals drop to 40% of normal and sales pause until it is over.
- 🔧 **Year end:** more arrivals in the last quarter, when dealers stock up for year-end
  sales.
- 🔧 **Growth:** arrivals grow by about 5% a year. For reference, VAMA members' sales grew
  5.3% in 2025.

### Selling 🔧

No public data exists on how long cars take to sell at Vietnamese dealers, so every model
shares one assumed pattern: most cars sell within a few weeks, and a long tail takes much
longer. A sale that would fall during Tet waits until after it.

Measured on the default data (seed 42, reference date 2026-09-27):

| Measure | Value |
|---|---|
| Cars in the data | 10,063 |
| Sold | 95.6% |
| In stock | 440 (45 aging, 20 approaching, 3 with no stock-in date) |
| Half of the cars sell within | 39 days |
| The middle half sell within | 23 to 65 days |
| Stays longer than 90 days | 14.2% |
| Value of aging stock | about 26.2 billion VND |
| Sales in the Tet month (Jan 2025) against the month before | down 28% (public figure for the whole market: down 40%) |

### Actions 🔧

Actions only happen while a car is in stock and at least 76 days old, matching the
service's own rule (SPEC D-8).

| When | What may happen |
|---|---|
| Day 76 to 85 | Half the time, a manager marks it `UNDER_REVIEW`. |
| Day 91 to 100 | Most of the time, a manager picks an action: usually a price reduction, sometimes a promotion, a transfer or something else. |
| Day 150 onwards | If still unsold, it is often sent to auction. |

**Assumed effect of actions** (this is the part the warning above is about):

| Action | Effect on the remaining time to sell |
|---|---|
| Price reduction planned | About half as long |
| Marketing promotion | About 30% shorter |
| Transfer to another dealership | About 20% shorter. The car stays recorded at its first dealership; moves between dealerships are not modelled. |
| Send to auction | Sold within one to three weeks |
| Under review, other | No effect |

### Unusual cases, on purpose 🔧

- **Trade-ins:** about 2% of sold cars come back later with the same VIN, at 60–75% of
  their earlier price. Each return is a new stay in stock (SPEC D-11).
- **Missing stock-in dates:** a few cars in stock have no stock-in date, so the `unknown`
  status appears in the data (SPEC D-6). Only cars without actions are chosen.

## Checks

The data goes through the same loader checks as any other data (SPEC AC-2.6), and
`tests/test_simulation.py` checks that:

- No car is sold before it arrives, and nothing happens after the reference date.
- Every action happens while its car is in stock and at least 76 days old.
- Every price is a whole number of VND inside its model's price list (trade-ins lower).
- No model arrives before it went on sale.
- Sales drop in the weeks around Tet.
- Counts land in realistic ranges, trade-ins and missing dates are present, and the same
  seed always gives the same data.

## Sources

All accessed September 2026.

- Market total and growth, 2025: [VietnamPlus, "Vietnam's auto market sees double-digit growth in 2025"](https://en.vietnamplus.vn/vietnams-auto-market-posts-double-digit-growth-in-2025-post335942.vnp); [Best Selling Cars Blog, Vietnam full year 2025](https://bestsellingcarsblog.com/2026/01/vietnam-full-year-2025-vinfast-at-29-share-monopolises-top-4-with-vf-3-at-1/) (VinFast 29% share, Limo Green launched in September 2025).
- Units by model, 2025: [Motorist Vietnam, top 10 best-selling cars 2025](https://www.motorist.vn/en/article/5435/top-10-best-selling-cars-in-vietnam-2025-vinfast-dominates-the-market); [VietnamNet, best-selling model of each brand in 2025](https://vietnamnet.vn/en/vietnam-s-2025-car-sales-race-these-9-models-led-their-brands-2483168.html) (also the VF 3 launch in August 2024).
- Tet effect: [VietnamPlus, "Car sales in Vietnam down 40% in January"](https://en.vietnamplus.vn/car-sales-in-vietnam-down-40-in-january-post309860.vnp).
- List prices: [giaxeoto.vn](https://giaxeoto.vn/index.php/gia-xe) (VF 3, VF 5, Xpander, Ranger, CX-5, Vios, City, Seltos); [oto.com.vn, VinFast price list](https://oto.com.vn/bang-gia-xe-o-to-vinfast-moi-nhat) (VF 6, Limo Green); [techz.vn](https://www.techz.vn/220-726-5-gia-xe-mitsubishi-moi-nhat-thang-7-2026-xforce-tu-605-trieu-xpander-khoi-diem-568-trieu-dong-ylt700458.html) (Xforce); [oto.com.vn, Yaris Cross](https://oto.com.vn/bang-gia-xe-o-to-toyota-yaris-cross-moi-nhat); [nguoiduatin.vn, Tucson](https://www.nguoiduatin.vn/gia-xe-hyundai-tucson-thang-9-2026-uu-dai-toi-85-trieu-dong-204262309065003088.htm); [oto360.net, XL7 Hybrid](https://oto360.net/xe-suzuki/xl7-hybrid.html).
  The Xforce, Yaris Cross and Tucson ranges were read from search-result summaries of these
  pages and not checked on the pages themselves; the others were read on the pages.
