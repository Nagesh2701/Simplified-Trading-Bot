# Simplified Trading Bot (Binance Futures Testnet)
This project is a small Python CLI app that places `MARKET` and `LIMIT` orders on Binance Futures Testnet (USDT-M) using signed REST API calls.

## Features
- Python 3.x CLI with argument validation
- Supports `BUY` and `SELL`
- Supports `MARKET` and `LIMIT`
- Structured app layers:
  - `bot/client.py` for Binance API client
  - `bot/orders.py` for order flow and response summary
  - `bot/validators.py` for input validation
  - `bot/logging_config.py` for file logging
  - `cli.py` as entry point
- Logs API requests, responses, and errors to `logs/trading_bot.log`
- Handles validation, API, and network errors with clear messages

## Testnet Base URL
All requests are sent to:
`https://testnet.binancefuture.com`

## Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Set Binance testnet credentials as environment variables:
   - `BINANCE_API_KEY`
   - `BINANCE_API_SECRET`

PowerShell example:
`$env:BINANCE_API_KEY="your_key"`
`$env:BINANCE_API_SECRET="your_secret"`

## Run Examples
MARKET BUY:
`python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001`

LIMIT SELL:
`python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 120000`

## Integration Test Script
Use the script below to verify MARKET and LIMIT order placement against Binance Futures Testnet in one run:
`python test_order_placement.py --symbol BTCUSDT --market-side BUY --market-quantity 0.001 --limit-side SELL --limit-quantity 0.001 --limit-price 120000`

The script validates responses and prints PASS/FAIL per order type.
If the LIMIT test order remains unfilled (`NEW`/`PARTIALLY_FILLED`), it is cancelled automatically for cleanup.

## Output
The CLI prints:
- order request summary
- order response details (`orderId`, `status`, `executedQty`, `avgPrice`)
- success/failure message

## Log Files
Logs are written to:
- `logs/trading_bot.log`

For submission, include logs captured from:
- at least one successful `MARKET` order attempt
- at least one successful `LIMIT` order attempt

## Assumptions
- Binance Futures Testnet account is active and API keys are valid.
- Symbol/quantity precision and exchange filters are enforced by Binance API.
- This task implementation focuses on single-order placement via CLI.
