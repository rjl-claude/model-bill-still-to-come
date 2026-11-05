"""One frozen record of every contested choice, central by default (design: Scenario), and the brackets.

The defaults are the build plan's rulings (points 1-26). A bracket is a pair of Scenarios, each moving
one input from central; `BRACKETS` declares every bracket whose input the model already has, once.
`LATER` lists the rest with the stage that adds them, so none is forgotten.
"""
from dataclasses import dataclass, field, replace
from typing import NamedTuple

from . import prices
from .cm import SHARE_CENTRAL as CM_SHARE, SHARE_HIGH as CM_HIGH, SHARE_LOW as CM_LOW
from .contracts import HPC_STRIKE_2012
from .discount import MarketResponse, SimpleFit
from .output import DECLINES
from .ro import RECYCLE_CENTRAL, RECYCLE_HIGH, RECYCLE_LOW


@dataclass(frozen=True)
class Scenario:
    case: str = "Reference"  # Annex M fossil-price case, the price path when `prices` is not given
    prices: tuple[tuple[int, float], ...] | None = None  # any price path: (year, £/MWh 2024 CPIH) pairs
    market: MarketResponse = field(default_factory=SimpleFit)  # discount and unpaid negative hours
    decline: str = "central"  # point 17: wind and solar decline with age, `output.DECLINES` (facts 22, 33, 34)
    output: str = "measured"  # build plan "Output": each farm's own record; bracket "DESNZ 2023" (fact 35)
    abandonment: bool = False  # point 16 bracket: unbuilt renewables cut by their termination rate
    late_starts: bool = False  # point 16 bracket: unbuilt contracts start late by their round's delay
    hpc_strike_2012: float = HPC_STRIKE_2012  # point 23
    hpc_term: str = "contract"  # point 24; bracket "from_start"
    hpc_shift_years: int = 0  # point 13 bracket: -1 or +2
    ro_recycle: float = RECYCLE_CENTRAL  # RO recycle value, share of the buy-out price
    cm_share: float = CM_SHARE  # point 9: net zero's share of the Capacity Market, the Clock's 2025
    szc_cost: float = 40_509_000_000  # point 10: the licence's Original Lower Regulatory Threshold
    szc_ops_return: float = 0.0673  # Richard 5 Nov, choice (a): the IWACC held after 2039 (stated)
    households: str = "held"  # point 18: households' share held at 2025's; bracket "EEP" (DESNZ's projection)
    bics_a_year: float = 600_000_000  # point 20, fact 20: the manufacturers' exemption, £ cash a year

    @property
    def wind_decline(self) -> float:
        return DECLINES[self.decline][0]

    @property
    def solar_decline(self) -> float:
        return DECLINES[self.decline][1]

    def price_path(self) -> dict[int, float]:
        return dict(self.prices) if self.prices is not None else prices.annex_m_path(self.case)

    def power(self, year: int) -> float:
        """Baseload power price for `year`, £/MWh 2024 CPIH; outside the path, its nearest year's."""
        path = self._path()
        return path[min(max(year, min(path)), max(path))]

    def _path(self) -> dict[int, float]:
        cached = self.__dict__.get("_path_cache")
        if cached is None:
            cached = self.price_path()
            object.__setattr__(self, "_path_cache", cached)
        return cached


class Bracket(NamedTuple):
    name: str
    low: Scenario  # the input's low end (or central, for a one-sided bracket)
    high: Scenario  # the input's high end (or central)


_C = Scenario()
# Points 7, 25: the NESO FES 2025 pathways giving the lowest and highest bill, found by running (stage 6).
BUILD_LOW, BUILD_HIGH = "Falling Behind", "Holistic Transition"
BRACKETS = (
    Bracket("Annex M prices", replace(_C, case="FFP_Low"), replace(_C, case="FFP_High")),
    Bracket("Discount slope", replace(_C, market=SimpleFit(discount_bound=-1)), replace(_C, market=SimpleFit(discount_bound=1))),
    Bracket("Negative-hours slope", replace(_C, market=SimpleFit(negative_bound=-1)), replace(_C, market=SimpleFit(negative_bound=1))),
    Bracket("Unbuilt abandoned", replace(_C, abandonment=True), _C),
    Bracket("Unbuilt start late", _C, replace(_C, late_starts=True)),
    Bracket("Hinkley strike", _C, replace(_C, hpc_strike_2012=92.50)),
    Bracket("Hinkley term", _C, replace(_C, hpc_term="from_start")),
    Bracket("Hinkley start", replace(_C, hpc_shift_years=-1), replace(_C, hpc_shift_years=2)),
    Bracket("RO recycle value", replace(_C, ro_recycle=RECYCLE_LOW), replace(_C, ro_recycle=RECYCLE_HIGH)),
    Bracket("Capacity Market share", replace(_C, cm_share=CM_LOW), replace(_C, cm_share=CM_HIGH)),
    Bracket("Sizewell C build cost", replace(_C, szc_cost=38_000_000_000), replace(_C, szc_cost=47_720_000_000)),
    Bracket("Households' share", replace(_C, households="EEP"), _C),
    Bracket("Forward prices, then Annex M", replace(_C, prices=tuple(prices.forward_then_annex_m().items())), _C),
    Bracket("Decline with age", replace(_C, decline="gentler"), replace(_C, decline="steeper")),
    Bracket("Output level", _C, replace(_C, output="DESNZ 2023")),
    Bracket("Build path", replace(_C, market=SimpleFit(path=BUILD_LOW)), replace(_C, market=SimpleFit(path=BUILD_HIGH))),
    Bracket("Sizewell C return after 2039", replace(_C, szc_ops_return=0.035), _C),  # Richard 5 Nov: 3.5% to 6.73%
)

LATER: tuple = ()  # every bracket in the build plan is declared (stage 6)
