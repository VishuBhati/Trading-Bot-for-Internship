"""
orders.py - High-level order placement logic.

Sits between the CLI layer and the low-level BinanceClient.
Responsible for building the order summary, calling the client,
and returning a structured result.
"""

from typing import Any, Dict, Optional

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logger

logger = setup_logger("trading_bot.orders")


class OrderResult:
    """
    Wraps the outcome of an order placement attempt.

    Attributes:
        success:    True if the order was accepted by the exchange.
        order_id:   Binance order ID (present on success).
        status:     Order status string from the exchange.
        executed_qty: Filled quantity (string, as returned by Binance).
        avg_price:  Average fill price (string, as returned by Binance).
        raw:        Full raw response dict.
        error:      Error message (present on failure).
    """

    def __init__(
        self,
        success: bool,
        raw: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.raw = raw or {}
        self.error = error

        self.order_id: Optional[int] = self.raw.get("orderId")
        self.status: Optional[str] = self.raw.get("status")
        self.executed_qty: Optional[str] = self.raw.get("executedQty")
        self.avg_price: Optional[str] = self.raw.get("avgPrice")

    def __repr__(self) -> str:  # pragma: no cover
        if self.success:
            return (
                f"OrderResult(success=True, orderId={self.order_id}, "
                f"status={self.status}, executedQty={self.executed_qty}, "
                f"avgPrice={self.avg_price})"
            )
        return f"OrderResult(success=False, error={self.error!r})"


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> OrderResult:
    """
    Place an order via *client* and return an :class:`OrderResult`.

    All exceptions from the client layer are caught and translated into
    a failed :class:`OrderResult` so the CLI can display them cleanly.

    Args:
        client:     Initialised :class:`BinanceClient`.
        symbol:     Trading pair (e.g. 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Order quantity.
        price:      Limit price (required for LIMIT orders, ignored otherwise).

    Returns:
        :class:`OrderResult` indicating success or failure.
    """
    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        return OrderResult(success=True, raw=raw)

    except BinanceAPIError as exc:
        logger.error("Binance API rejected the order: %s", exc)
        return OrderResult(success=False, error=str(exc))

    except Exception as exc:  # network errors, timeouts, etc.
        logger.error("Unexpected error while placing order: %s", exc, exc_info=True)
        return OrderResult(success=False, error=f"Unexpected error: {exc}")
