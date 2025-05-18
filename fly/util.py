from decimal import Decimal, ROUND_HALF_UP


def round_half_up(n: float) -> float:
    """Round using ROUND_HALF_UP to match game UI."""
    return Decimal(str(n)).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)
