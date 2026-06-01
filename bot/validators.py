"""
validators.py - Input validation for trading bot CLI parameters.
"""

from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise the trading symbol.

    Args:
        symbol: e.g. 'btcusdt' or 'BTCUSDT'

    Returns:
        Upper-cased symbol string.

    Raises:
        ValidationError: if the symbol is empty or contains spaces.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol must not be empty.")
    if " " in symbol:
        raise ValidationError(f"Symbol '{symbol}' must not contain spaces.")
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive)

    Returns:
        Upper-cased side string.

    Raises:
        ValidationError: if side is not BUY or SELL.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: 'MARKET' or 'LIMIT' (case-insensitive)

    Returns:
        Upper-cased order type string.

    Raises:
        ValidationError: if order type is not MARKET or LIMIT.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> float:
    """
    Validate order quantity.

    Args:
        quantity: Quantity as string.

    Returns:
        Quantity as float.

    Raises:
        ValidationError: if quantity is not a positive number.
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {qty}.")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate price, required for LIMIT orders.

    Args:
        price: Price as string, or None.
        order_type: 'MARKET' or 'LIMIT'.

    Returns:
        Price as float, or None for MARKET orders.

    Raises:
        ValidationError: if LIMIT order has no price, or price is invalid/non-positive.
    """
    if order_type == "LIMIT":
        if price is None or str(price).strip() == "":
            raise ValidationError("Price is required for LIMIT orders.")
        try:
            p = float(price)
        except (ValueError, TypeError):
            raise ValidationError(f"Price '{price}' is not a valid number.")
        if p <= 0:
            raise ValidationError(f"Price must be greater than 0, got {p}.")
        return p

    # MARKET order — price is ignored
    return None
