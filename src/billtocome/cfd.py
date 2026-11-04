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


def top_up_with_rule(strike: float, market: float, capture: float, mwh: float,
                     neg_share: float, neg_price: float) -> float:
    """Top-up when the contract is not paid in some negative-price hours (aios-harness#67).

    neg_share: the share of `mwh` generated in hours the contract's rule leaves unpaid
    neg_price: the average (negative) price in those hours, £/MWh
    The plain top-up counts every hour at (strike - price); the unpaid hours' share is taken off.
    """
    return top_up(strike, market, capture, mwh) - neg_share * mwh * (strike - neg_price)


def contract_end(start: date, years: int) -> date:
    """The day the term ends: the same calendar day, `years` later."""
    return start.replace(year=start.year + years)


def in_term(year: int, start: date, years: int) -> float:
    """Share of calendar `year` inside the term (0 to 1)."""
    end = contract_end(start, years)
    y0, y1 = date(year, 1, 1), date(year + 1, 1, 1)
    lo, hi = max(y0, start), min(y1, end)
    return max(0, (hi - lo).days) / (y1 - y0).days
