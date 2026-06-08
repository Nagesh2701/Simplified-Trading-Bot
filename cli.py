from __future__ import annotations

import argparse
import os
import sys

from bot.client import BinanceAPIError, BinanceFuturesClient
from bot.logging_config import configure_logging
from bot.orders import build_order_response_summary, place_futures_order
from bot.validators import ValidationError, validate_inputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading symbol (e.g., BTCUSDT)")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument("--type", required=True, help="MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument(
        "--price",
        required=False,
        help="Order price (required for LIMIT, forbidden for MARKET)",
    )
    return parser.parse_args()


def main() -> int:
    logger = configure_logging()
    args = parse_args()

    try:
        symbol, side, order_type, quantity, price = validate_inputs(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        print(f"Input validation error: {exc}")
        logger.error("Input validation error: %s", exc)
        return 2

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        message = (
            "Missing API credentials. Set BINANCE_API_KEY and BINANCE_API_SECRET "
            "environment variables."
        )
        print(message)
        logger.error(message)
        return 2

    print("Order Request Summary:")
    print(f"  symbol: {symbol}")
    print(f"  side: {side}")
    print(f"  type: {order_type}")
    print(f"  quantity: {quantity}")
    if price is not None:
        print(f"  price: {price}")

    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
    try:
        response = place_futures_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except BinanceAPIError as exc:
        print(f"Order placement failed: {exc}")
        logger.exception("Order placement failed")
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        logger.exception("Unexpected runtime error")
        return 1

    print(build_order_response_summary(response))
    print("Order placement succeeded.")
    logger.info("Order placement succeeded | orderId=%s", response.get("orderId"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

