#!/usr/bin/env python3
"""
Zerodha Kite Connect Authentication Helper
Generates the daily access token required to access Zerodha Kite APIs.

Usage:
    Interactive mode:
        python authenticate.py

    Non-interactive mode (pass request token via flag):
        python authenticate.py --request-token <your_request_token>
"""

import argparse
import os
import sys
import urllib.parse
from dotenv import find_dotenv, load_dotenv, set_key
from kiteconnect import KiteConnect
import kiteconnect.exceptions as kite_exceptions


def get_env_file_path() -> str:
    """Find existing .env or return path to create one in current working directory."""
    env_path = find_dotenv()
    if not env_path:
        env_path = os.path.join(os.getcwd(), ".env")
        if not os.path.exists(env_path):
            # Create an empty .env file if it doesn't exist
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("# Zerodha Kite Connect Credentials\n")
    return env_path


def parse_request_token(user_input: str) -> str:
    """
    Extract request_token whether user provided the raw token or the full redirected URL.
    """
    cleaned = user_input.strip().strip("'\"")
    if "request_token=" in cleaned:
        parsed_url = urllib.parse.urlparse(cleaned)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if "request_token" in query_params:
            return query_params["request_token"][0]
    return cleaned


def main():
    parser = argparse.ArgumentParser(
        description="Authenticate Zerodha Kite Connect and store the daily access token in .env"
    )
    parser.add_argument(
        "--request-token",
        "-t",
        help="Request token obtained from Zerodha redirect URL",
        default=None,
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not attempt to automatically open browser",
    )
    args = parser.parse_args()

    env_path = get_env_file_path()
    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("KITE_API_KEY", "").strip()
    api_secret = os.getenv("KITE_API_SECRET", "").strip()

    print("=" * 70)
    print("       ZERODHA KITE CONNECT - DAILY AUTHENTICATION HELPER")
    print("=" * 70)

    if not api_key:
        api_key = input("Enter your KITE_API_KEY: ").strip()
        if not api_key:
            print("[ERROR] KITE_API_KEY cannot be empty.", file=sys.stderr)
            sys.exit(1)
        set_key(env_path, "KITE_API_KEY", api_key)
        print(f"[OK] Saved KITE_API_KEY to {env_path}")

    if not api_secret:
        api_secret = input("Enter your KITE_API_SECRET: ").strip()
        if not api_secret:
            print("[ERROR] KITE_API_SECRET cannot be empty.", file=sys.stderr)
            sys.exit(1)
        set_key(env_path, "KITE_API_SECRET", api_secret)
        print(f"[OK] Saved KITE_API_SECRET to {env_path}")

    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()

    print("\n--- STEP 1: Login Authorization ---")
    print(f"Open this URL in your web browser:\n\n  {login_url}\n")

    if not args.no_browser and not args.request_token:
        try:
            import webbrowser
            print("Opening browser for authorization...")
            webbrowser.open(login_url)
        except Exception:
            pass

    print("--- STEP 2: Obtain Request Token ---")
    print("1. Log in with your Zerodha user ID, password, and 2FA/TOTP.")
    print("2. Zerodha will redirect to your app's Redirect URL.")
    print("   Example: http://127.0.0.1:8000/?request_token=XXXXX&action=login\n")

    request_token_raw = args.request_token
    if not request_token_raw:
        request_token_raw = input("Paste the redirected URL (or just the request_token): ").strip()

    request_token = parse_request_token(request_token_raw)
    if not request_token:
        print("[ERROR] No request token provided.", file=sys.stderr)
        sys.exit(1)

    print("\n--- STEP 3: Generating Session & Access Token ---")
    try:
        session_data = kite.generate_session(request_token=request_token, api_secret=api_secret)
        access_token = session_data.get("access_token")

        if not access_token:
            print("[ERROR] Failed to extract access_token from session response.", file=sys.stderr)
            sys.exit(1)

        # Store in .env
        set_key(env_path, "KITE_ACCESS_TOKEN", access_token)

        user_name = session_data.get("user_name", "N/A")
        user_id = session_data.get("user_id", "N/A")
        email = session_data.get("email", "N/A")

        print("=" * 70)
        print(" [SUCCESS] AUTHENTICATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"  User:         {user_name} ({user_id})")
        print(f"  Email:        {email}")
        print(f"  Access Token: {access_token[:6]}...{access_token[-4:]}")
        print(f"  Saved to:     {env_path}")
        print("=" * 70)
        print("Your Kite MCP server can now connect and fetch portfolio data.")

    except kite_exceptions.TokenException as exc:
        print(f"\n[ERROR] Invalid or expired request token: {exc}", file=sys.stderr)
        print("Request tokens expire within a few minutes and are single-use.", file=sys.stderr)
        sys.exit(1)
    except kite_exceptions.KiteException as exc:
        print(f"\n[ERROR] Kite API error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Unexpected error generating session: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
