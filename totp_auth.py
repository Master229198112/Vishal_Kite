"""
Headless Zerodha Kite Authentication Module
Implements pure Python RFC 6238 Time-Based One-Time Password (TOTP) generation
and automated browserless session token renewal.
"""

import base64
import hashlib
import hmac
import struct
import time
from urllib.parse import parse_qs, urlparse
from typing import Optional, Tuple
import httpx
from kiteconnect import KiteConnect

from config import get_config, set_access_token


def generate_totp(secret: str) -> str:
    """
    Generate standard 6-digit RFC 6238 TOTP using Python standard library.
    Zero external dependencies needed (no pyotp required).
    """
    clean_secret = secret.replace(" ", "").strip().upper()
    key = base64.b32decode(clean_secret, casefold=True)
    # 30-second interval counter
    counter = int(time.time() // 30)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[19] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def perform_headless_kite_login(
    user_id: Optional[str] = None,
    password: Optional[str] = None,
    totp_secret: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
) -> Tuple[bool, str, Optional[str]]:
    """
    Authenticate headlessly against Zerodha Kite and exchange request token for daily access token.
    Reads credentials from arguments, .env, or Streamlit Secrets.
    """
    uid = user_id or get_config("ZERODHA_USER_ID") or get_config("KITE_USER_ID", "DF2893")
    pwd = password or get_config("ZERODHA_PASSWORD")
    sec = totp_secret or get_config("ZERODHA_TOTP_SECRET")
    k_api = api_key or get_config("KITE_API_KEY")
    k_sec = api_secret or get_config("KITE_API_SECRET")

    if not k_api or not k_sec:
        return False, "KITE_API_KEY or KITE_API_SECRET is missing.", None

    if not uid or not pwd or not sec:
        return (
            False,
            "Missing Zerodha credentials. Provide ZERODHA_USER_ID, ZERODHA_PASSWORD, and ZERODHA_TOTP_SECRET.",
            None,
        )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }

    try:
        with httpx.Client(headers=headers, timeout=15.0, follow_redirects=False) as client:
            # 1. First factor login (User ID + Password)
            login_url = "https://kite.zerodha.com/api/login"
            resp1 = client.post(login_url, data={"user_id": uid, "password": pwd})
            data1 = resp1.json()

            if resp1.status_code != 200 or data1.get("status") != "success":
                msg = data1.get("message", "Zerodha login failed. Check user ID and password.")
                return False, f"Step 1 (Password) failed: {msg}", None

            request_id = data1.get("data", {}).get("request_id")
            if not request_id:
                return False, "Failed to retrieve 2FA request_id from Zerodha.", None

            # 2. Second factor 2FA using auto-generated RFC 6238 TOTP
            totp_code = generate_totp(sec)
            twofa_url = "https://kite.zerodha.com/api/twofa"
            resp2 = client.post(
                twofa_url,
                data={
                    "user_id": uid,
                    "request_id": request_id,
                    "twofa_value": totp_code,
                    "skip_session": "true",
                },
            )
            data2 = resp2.json()

            if resp2.status_code != 200 or data2.get("status") != "success":
                msg = data2.get("message", "Invalid TOTP code or expired secret.")
                return False, f"Step 2 (TOTP 2FA) failed: {msg}", None

            # 3. Retrieve Connect OAuth authorization redirect
            connect_auth_url = f"https://kite.zerodha.com/connect/login?v=3&api_key={k_api}"
            resp3 = client.get(connect_auth_url)

            # Expected 302 Redirect containing request_token
            location = resp3.headers.get("location") or resp3.headers.get("Location")
            if not location:
                return False, "Kite Connect authorization redirect was not received.", None

            parsed_url = urlparse(location)
            params = parse_qs(parsed_url.query)
            request_tokens = params.get("request_token")

            if not request_tokens:
                return False, f"Request token not found in redirect URL: {location}", None

            request_token = request_tokens[0]

            # 4. Exchange request_token for Kite daily access_token
            kite = KiteConnect(api_key=k_api)
            session_data = kite.generate_session(request_token, api_secret=k_sec)
            access_token = session_data["access_token"]

            # Save access token
            set_access_token(access_token)
            return True, "Headless login successful! Daily token generated and active.", access_token

    except Exception as exc:
        return False, f"Headless login error: {str(exc)}", None
