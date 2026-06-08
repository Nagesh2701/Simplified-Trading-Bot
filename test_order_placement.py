from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from bot.client import BinanceAPIError, BinanceFuturesClient
from bot.logging_config import configure_logging
from bot.orders import place_futures_order
from bot.validators import ValidationError, parse_positive_decimal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Integration test script for Binance Futures Testnet order placement "
            "(MARKET + LIMIT)."
        )
    )
    parser.add_argument("--symbol", required=True, help="Symbol, e.g. BTCUSDT")
    parser.add_argument(
        "--market-side",
        default="BUY",
        choices=["BUY", "SELL"],
        help="Side for MARKET test order",
    )
    parser.add_argument(
        "--market-quantity",
        required=True,
        help="Quantity for MARKET test order",
    )
    parser.add_argument(
        "--limit-side",
        default="SELL",
        choices=["BUY", "SELL"],
        help="Side for LIMIT test order",
    )
    parser.add_argument(
        "--limit-quantity",
        required=True,
        help="Quantity for LIMIT test order",
    )
    parser.add_argument(
        "--limit-price",
        required=True,
        help="Price for LIMIT test order",
    )
    return parser.parse_args()


def assert_order_response_fields(order: dict[str, Any], expected_type: str) -> None:
    required_fields = ("orderId", "status", "symbol", "side", "type", "executedQty")
    missing = [field for field in required_fields if field not in order]
    if missing:
        raise AssertionError(f"Missing fields in {expected_type} response: {missing}")

    if order.get("type") != expected_type:
        raise AssertionError(
            f"Expected type={expected_type}, got type={order.get('type')}"
        )

    status = str(order.get("status"))
    if status not in {"NEW", "PARTIALLY_FILLED", "FILLED"}:
        raise AssertionError(f"Unexpected order status for {expected_type}: {status}")


def main() -> int:
    logger = configure_logging()
    args = parse_args()

    try:
        parse_positive_decimal(args.market_quantity, "market-quantity")
        parse_positive_decimal(args.limit_quantity, "limit-quantity")
        parse_positive_decimal(args.limit_price, "limit-price")
    except ValidationError as exc:
        print(f"Input validation failed: {exc}")
        logger.error("Integration test input validation failed: %s", exc)
        return 2

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        print("Missing BINANCE_API_KEY or BINANCE_API_SECRET environment variable.")
        logger.error("Missing API credentials for integration test.")
        return 2

    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)

    print("Running Binance Futures Testnet integration checks...")
    print(f"  symbol: {args.symbol.upper()}")
    print(
        f"  market: {args.market_side} {args.market_quantity} | "
        f"limit: {args.limit_side} {args.limit_quantity} @ {args.limit_price}"
    )

    limit_response: dict[str, Any] | None = None
    try:
        market_response = place_futures_order(
            client=client,
            symbol=args.symbol.upper(),
            side=args.market_side,
            order_type="MARKET",
            quantity=args.market_quantity,
            price=None,
        )
        assert_order_response_fields(market_response, expected_type="MARKET")
        print(
            "MARKET order test: PASS | "
            f"orderId={market_response.get('orderId')} status={market_response.get('status')}"
        )

        limit_response = place_futures_order(
            client=client,
            symbol=args.symbol.upper(),
            side=args.limit_side,
            order_type="LIMIT",
            quantity=args.limit_quantity,
            price=args.limit_price,
        )
        assert_order_response_fields(limit_response, expected_type="LIMIT")
        print(
            "LIMIT order test: PASS  | "
            f"orderId={limit_response.get('orderId')} status={limit_response.get('status')}"
        )

    except BinanceAPIError as exc:
        print(f"Integration test failed due to Binance API error: {exc}")
        logger.exception("Integration test Binance API error")
        return 1
    except AssertionError as exc:
        print(f"Integration test assertion failed: {exc}")
        logger.exception("Integration test assertion failed")
        return 1
    except Exception as exc:
        print(f"Integration test failed with unexpected error: {exc}")
        logger.exception("Integration test unexpected error")
        return 1
    finally:
        if limit_response is not None:
            limit_status = str(limit_response.get("status"))
            if limit_status in {"NEW", "PARTIALLY_FILLED"}:
                limit_order_id = limit_response.get("orderId")
                try:
                    cancel_response = client.cancel_order(
                        symbol=args.symbol.upper(),
                        order_id=limit_order_id,
                    )
                    print(
                        "LIMIT cleanup: CANCELLED | "
                        f"orderId={cancel_response.get('orderId', limit_order_id)} "
                        f"status={cancel_response.get('status')}"
                    )
                    logger.info(
                        "LIMIT cleanup succeeded | orderId=%s status=%s",
                        cancel_response.get("orderId", limit_order_id),
                        cancel_response.get("status"),
                    )
                except Exception as cleanup_exc:
                    print(
                        "LIMIT cleanup warning: failed to cancel unfilled test order "
                        f"(orderId={limit_order_id}): {cleanup_exc}"
                    )
                    logger.exception(
                        "LIMIT cleanup failed | orderId=%s", limit_order_id
                    )

    print("All order placement integration checks passed.")
    logger.info("Order placement integration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

