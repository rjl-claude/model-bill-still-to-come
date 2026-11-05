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
from .output import DECLINE
from .ro import RECYCLE_CENTRAL, RECYCLE_HIGH, RECYCLE_LOW


@dataclass(frozen=True)
class Scenario:
    case: str = "Reference"  # Annex M fossil-price case, the price path when `prices` is not given
    prices: tuple[tuple[int, float], ...] | None = None  # any price path: (year, £/MWh 2024 CPIH) pairs
    market: MarketResponse = field(default_factory=SimpleFit)  # discount and unpaid negative hours
    wind_decline: float = DECLINE  # point 17: Staffell & Green 2014
    solar_decline: float = 0.005  # point 17: Jordan & Kurtz 2013 (facts 22)
    abandonment: bool = False  # point 16 bracket: unbuilt renewables cut by their termination rate
    late_starts: bool = False  # point 16 bracket: unbuilt contracts start late by their round's delay
    hpc_strike_2012: float = HPC_STRIKE_2012  # point 23
    hpc_term: str = "contract"  # point 24; bracket "from_start"
    hpc_shift_years: int = 0  # point 13 bracket: -1 or +2
    ro_recycle: float = RECYCLE_CENTRAL  # RO recycle value, share of the buy-out price
    cm_share: float = CM_SHARE  # point 9: net zero's share of the Capacity Market, the Clock's 2025

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
)

LATER = (
    ("Sizewell C build cost", 3),
    ("Households' share", 4),
    ("Forward prices, then Annex M", 6),
    ("Decline with age", 6),  # Hamilton 0.2-0.5%/yr gentler; Hughes (REF 2012) steeper: its rate not yet in facts
    ("Output level", 6),  # DESNZ's assumed load factors as the high end
    ("Build path", 6),  # NESO FES pathways (point 25), which end is low found by running
)
