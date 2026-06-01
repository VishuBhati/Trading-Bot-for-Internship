"""
cli.py - Command-line interface entry point for the Binance Futures trading bot.

Usage examples:
    # Market BUY
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

    # Limit SELL
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3500

    # Override API credentials via flags (or use env vars)
    python cli.py --api-key <KEY> --api-secret <SECRET> --symbol BTCUSDT ...
"""

import argparse
import os
import sys
from typing import Optional

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import place_order
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)

logger = setup_logger("trading_bot.cli")

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

SEPARATOR = "─" * 60


def _print_separator() -> None:
    print(SEPARATOR)


def _print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> None:
    """Print a human-readable order request summary."""
    _print_separator()
    print("  ORDER REQUEST SUMMARY")
    _print_separator()
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    print(f"  Price      : {price if price is not None else 'MARKET (best available)'}")
    _print_separator()


def _print_order_result(result) -> None:
    """Print the exchange response details."""
    if result.success:
        print("\n  ✅  ORDER PLACED SUCCESSFULLY")
        _print_separator()
        print(f"  Order ID     : {result.order_id}")
        print(f"  Status       : {result.status}")
        print(f"  Executed Qty : {result.executed_qty}")
        if result.avg_price and result.avg_price != "0":
            print(f"  Avg Price    : {result.avg_price}")
        _print_separator()
    else:
        print("\n  ❌  ORDER FAILED")
        _print_separator()
        print(f"  Reason : {result.error}")
        _print_separator()


# ──────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place Market / Limit orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Credentials (env vars are the recommended approach)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("BINANCE_API_KEY", ""),
        help="Binance API key (or set BINANCE_API_KEY env var).",
    )
    parser.add_argument(
        "--api-secret",
        default=os.environ.get("BINANCE_API_SECRET", ""),
        help="Binance API secret (or set BINANCE_API_SECRET env var).",
    )

    # Order parameters
    parser.add_argument(
        "--symbol", required=True, help="Trading pair, e.g. BTCUSDT."
    )
    parser.add_argument(
        "--side", required=True, help="Order side: BUY or SELL."
    )
    parser.add_argument(
        "--type", dest="order_type", required=True, help="Order type: MARKET or LIMIT."
    )
    parser.add_argument(
        "--quantity", required=True, help="Order quantity (e.g. 0.001)."
    )
    parser.add_argument(
        "--price",
        default=None,
        help="Limit price (required for LIMIT orders).",
    )

    return parser


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    CLI entry point.

    Returns:
        Exit code: 0 on success, 1 on validation / API error.
    """
    parser = build_parser()
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Validate credentials
    # ------------------------------------------------------------------
    if not args.api_key or not args.api_secret:
        print(
            "ERROR: API credentials are required.\n"
            "  Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables, or\n"
            "  pass --api-key and --api-secret flags."
        )
        logger.error("Missing API credentials — aborting.")
        return 1

    # ------------------------------------------------------------------
    # 2. Validate user inputs
    # ------------------------------------------------------------------
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
    except ValidationError as exc:
        print(f"INPUT ERROR: {exc}")
        logger.warning("Validation failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # 3. Print order summary
    # ------------------------------------------------------------------
    _print_order_summary(symbol, side, order_type, quantity, price)

    # ------------------------------------------------------------------
    # 4. Initialise client and place order
    # ------------------------------------------------------------------
    try:
        client = BinanceClient(api_key=args.api_key, api_secret=args.api_secret)
    except ValueError as exc:
        print(f"CLIENT ERROR: {exc}")
        logger.error("Failed to initialise BinanceClient: %s", exc)
        return 1

    result = place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )

    # ------------------------------------------------------------------
    # 5. Print result
    # ------------------------------------------------------------------
    _print_order_result(result)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
