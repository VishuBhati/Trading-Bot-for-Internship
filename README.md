# Binance Futures Testnet Trading Bot

A clean, structured Python CLI application for placing **Market** and **Limit** orders on the **Binance Futures Testnet (USDT-M)**.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper (signing, HTTP)
│   ├── orders.py          # Order placement logic + result model
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Rotating file + console logger
├── cli.py                 # CLI entry point (argparse)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.8+
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account with API credentials

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure credentials

Export your testnet API key and secret as environment variables (recommended):

```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

Or pass them as CLI flags (see examples below).

---

## Usage

```
python cli.py --symbol SYMBOL --side BUY|SELL --type MARKET|LIMIT --quantity QTY [--price PRICE]
```

### Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--symbol` | ✅ | Trading pair, e.g. `BTCUSDT` |
| `--side` | ✅ | `BUY` or `SELL` |
| `--type` | ✅ | `MARKET` or `LIMIT` |
| `--quantity` | ✅ | Order quantity, e.g. `0.001` |
| `--price` | ✅ for LIMIT | Limit price, e.g. `30000` |
| `--api-key` | optional | Override `BINANCE_API_KEY` env var |
| `--api-secret` | optional | Override `BINANCE_API_SECRET` env var |

### Examples

**Market BUY:**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Limit SELL:**
```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3500
```

**With inline credentials:**
```bash
python cli.py --api-key KEY --api-secret SECRET \
    --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 25000
```

---

## Sample Output

```
────────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : LIMIT
  Quantity   : 0.001
  Price      : 25000.0
────────────────────────────────────────────────────────────

  ✅  ORDER PLACED SUCCESSFULLY
────────────────────────────────────────────────────────────
  Order ID     : 3847291056
  Status       : NEW
  Executed Qty : 0.000
  Avg Price    : 0
────────────────────────────────────────────────────────────
```

---

## Logging

All API requests, responses, and errors are written to **`trading_bot.log`** (rotating, max 5 MB × 3 backups) and to the console (INFO level and above).

Log format:
```
2024-01-15 14:32:01 | INFO     | trading_bot.client | Placing BUY LIMIT order | symbol=BTCUSDT qty=0.001 price=25000.0
```

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Invalid symbol / side / type | `INPUT ERROR` printed; logged as WARNING; exit 1 |
| Missing price for LIMIT order | `INPUT ERROR` printed; logged as WARNING; exit 1 |
| Binance API error (4xx/5xx) | Error details printed; logged as ERROR; exit 1 |
| Network timeout / connection failure | Error details printed; logged as ERROR; exit 1 |
| Missing API credentials | Instructional error printed; exit 1 |

---

## Design Notes

- **Separation of concerns** — `client.py` owns HTTP/signing, `orders.py` owns business logic, `validators.py` owns input validation, `cli.py` owns UX.
- **No third-party Binance SDK** — uses only `requests` for full transparency and testnet compatibility.
- **Credentials never logged** — API key/secret are passed only in HTTP headers, never written to log files.
