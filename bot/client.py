"""
client.py - Low-level Binance Futures Testnet REST API client.

Handles HMAC-SHA256 request signing, HTTP communication, and raw
response / error parsing. No business logic lives here.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

logger = setup_logger("trading_bot.client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, status_code: int, code: int, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[HTTP {status_code}] Binance error {code}: {message}")


class BinanceClient:
    """
    Minimal wrapper around the Binance Futures Testnet REST API.

    Only the endpoints required by this task are implemented.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_BASE_URL):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must both be non-empty strings.")

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised (base_url=%s).", self.base_url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append a timestamp and HMAC-SHA256 signature to *params*."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        """
        Send an HTTP request and return the parsed JSON body.

        Args:
            method:   HTTP method ('GET', 'POST', …)
            endpoint: API path, e.g. '/fapi/v1/order'
            params:   Query / body parameters.
            signed:   Whether to add timestamp + signature.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            BinanceAPIError: on non-2xx responses with a Binance error body.
            requests.RequestException: on network-level failures.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.debug("→ %s %s  params=%s", method.upper(), url, params)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            else:
                response = self.session.request(
                    method.upper(), url, data=params, timeout=DEFAULT_TIMEOUT
                )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out after %ss: %s", DEFAULT_TIMEOUT, exc)
            raise

        logger.debug("← HTTP %s  body=%s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return {}

        # Binance returns error details inside the body even on 4xx/5xx
        if not response.ok:
            code = data.get("code", response.status_code)
            message = data.get("msg", response.text)
            logger.error(
                "Binance API error — HTTP %s, code=%s, msg=%s",
                response.status_code,
                code,
                message,
            )
            raise BinanceAPIError(response.status_code, code, message)

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """Return Binance server time in milliseconds (unsigned)."""
        data = self._request("GET", "/fapi/v1/time")
        return data["serverTime"]

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place a new futures order on the testnet.

        Args:
            symbol:        Trading pair, e.g. 'BTCUSDT'.
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET' or 'LIMIT'.
            quantity:      Order quantity.
            price:         Limit price (required for LIMIT orders).
            time_in_force: Time-in-force for LIMIT orders (default GTC).

        Returns:
            Order response dict from the Binance API.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s",
            side,
            order_type,
            symbol,
            quantity,
            price if price is not None else "MARKET",
        )

        response = self._request("POST", "/fapi/v1/order", params=params, signed=True)
        logger.info(
            "Order placed successfully | orderId=%s status=%s",
            response.get("orderId"),
            response.get("status"),
        )
        return response
