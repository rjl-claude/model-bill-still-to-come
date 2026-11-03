"""Contracts for Difference: the top-up bill-payers pay, contract by contract, year by year.

All money in 2024 prices. A CfD pays the generator its strike price less the market reference
price on each unit generated; when the market is above the strike, the generator pays back.
"""
from datetime import date


def top_up(strike: float, market: float, capture: float, mwh: float) -> float:
    """Top-up in £ for one contract-year.

    strike: the contract's strike price, £/MWh (2024 prices)
    market: the average (baseload) market price, £/MWh (2024 prices)
    capture: the share of the average price this technology earns (wind and solar earn less)
    mwh: the contract's generation in the year
    """
    return (strike - market * capture) * mwh


def contract_end(start: date, years: int) -> date:
    """The day the term ends: the same calendar day, `years` later."""
    return start.replace(year=start.year + years)


def in_term(year: int, start: date, years: int) -> float:
    """Share of calendar `year` inside the term (0 to 1)."""
    end = contract_end(start, years)
    y0, y1 = date(year, 1, 1), date(year + 1, 1, 1)
    lo, hi = max(y0, start), min(y1, end)
    return max(0, (hi - lo).days) / (y1 - y0).days
