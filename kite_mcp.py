#!/usr/bin/env python3
"""
Zerodha Kite MCP Server
Model Context Protocol (MCP) server providing read-only tools for Zerodha Kite:
- get_holdings: Portfolio holdings with buy price, LTP, P&L, quantity.
- get_positions: Open intraday & overnight positions with M2M / unrealised P&L.
- get_margins: Available cash and margin usage for equity & commodity.
- get_quote: Real-time LTP and OHLC market quotes.

SAFEGUARD:
This server is STRICTLY READ-ONLY. No order execution, modification,
or cancellation tools are exposed.
"""

import os
from typing import Any, Dict, List, Optional
from dotenv import find_dotenv, load_dotenv
from kiteconnect import KiteConnect
import kiteconnect.exceptions as kite_exceptions

try:
    from mcp.server.mcpserver import MCPServer
except (ImportError, ModuleNotFoundError):
    from mcp.server.fastmcp import FastMCP as MCPServer

# Initialize MCP server
mcp = MCPServer(
    "zerodha-kite",
    description="Zerodha Kite read-only portfolio analytics, position tracking, and market monitoring MCP server",
)


from config import get_access_token, get_config

def get_kite_client() -> KiteConnect:
    """
    Initialize and return authenticated KiteConnect client from environment or Streamlit secrets.
    Raises RuntimeError if credentials or daily access token are missing.
    """
    api_key = get_config("KITE_API_KEY")
    access_token = get_access_token()

    if not api_key:
        raise RuntimeError(
            "KITE_API_KEY is not configured in .env. "
            "Please add your API key from https://developers.kite.trade to your .env file."
        )

    if not access_token:
        raise RuntimeError(
            "KITE_ACCESS_TOKEN is missing or expired in .env. "
            "Please run 'python authenticate.py' to generate today's access token."
        )

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite


@mcp.tool()
def get_holdings() -> Dict[str, Any]:
    """
    Fetch equity and ETF holdings from Zerodha Kite.

    Returns:
        Dict containing portfolio summary (total investment, current value,
        total P&L, total P&L %) and itemized holdings with symbol, quantity,
        average price, current market price (LTP), and P&L.
    """
    try:
        kite = get_kite_client()
        raw_holdings = kite.holdings()

        total_investment = 0.0
        current_value = 0.0
        total_pnl = 0.0

        formatted_holdings = []
        for h in raw_holdings:
            qty = h.get("quantity", 0) + h.get("t1_quantity", 0)
            avg_price = float(h.get("average_price", 0.0))
            last_price = float(h.get("last_price", 0.0))
            pnl = float(h.get("pnl", 0.0))
            invested = qty * avg_price
            cur_val = qty * last_price

            total_investment += invested
            current_value += cur_val
            total_pnl += pnl

            formatted_holdings.append({
                "tradingsymbol": h.get("tradingsymbol"),
                "exchange": h.get("exchange"),
                "isin": h.get("isin"),
                "quantity": qty,
                "t1_quantity": h.get("t1_quantity", 0),
                "average_price": round(avg_price, 2),
                "last_price": round(last_price, 2),
                "close_price": round(float(h.get("close_price", 0.0)), 2),
                "pnl": round(pnl, 2),
                "pnl_percentage": round((pnl / invested * 100), 2) if invested > 0 else 0.0,
                "day_change": round(float(h.get("day_change", 0.0)), 2),
                "day_change_percentage": round(float(h.get("day_change_percentage", 0.0)), 2),
            })

        summary = {
            "total_holdings_count": len(formatted_holdings),
            "total_investment": round(total_investment, 2),
            "current_value": round(current_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percentage": round(
                (total_pnl / total_investment * 100) if total_investment > 0 else 0.0, 2
            ),
        }

        return {"status": "success", "summary": summary, "holdings": formatted_holdings}

    except kite_exceptions.TokenException:
        return {
            "status": "error",
            "error_type": "TokenExpired",
            "message": "Kite access token has expired or is invalid. Run 'python authenticate.py' to generate a new session.",
        }
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_positions() -> Dict[str, Any]:
    """
    Fetch open intraday (MIS/CO) and overnight (NRML/CNC) positions from Zerodha Kite.

    Returns:
        Dict containing position summary (total positions, open positions count,
        total unrealised P&L, realised P&L, M2M) and separated lists of open net
        positions, all net positions, and day positions.
    """
    try:
        kite = get_kite_client()
        positions_data = kite.positions()

        net_positions = positions_data.get("net", [])
        day_positions = positions_data.get("day", [])

        open_positions = [p for p in net_positions if p.get("quantity", 0) != 0]

        total_unrealised = sum(float(p.get("unrealised", 0.0)) for p in net_positions)
        total_realised = sum(float(p.get("realised", 0.0)) for p in net_positions)
        total_pnl = sum(float(p.get("pnl", 0.0)) for p in net_positions)
        total_m2m = sum(float(p.get("m2m", 0.0)) for p in net_positions)

        summary = {
            "total_net_positions": len(net_positions),
            "open_positions_count": len(open_positions),
            "total_unrealised_pnl": round(total_unrealised, 2),
            "total_realised_pnl": round(total_realised, 2),
            "total_pnl": round(total_pnl, 2),
            "total_m2m": round(total_m2m, 2),
        }

        return {
            "status": "success",
            "summary": summary,
            "open_positions": open_positions,
            "net_positions": net_positions,
            "day_positions": day_positions,
        }

    except kite_exceptions.TokenException:
        return {
            "status": "error",
            "error_type": "TokenExpired",
            "message": "Kite access token has expired or is invalid. Run 'python authenticate.py' to generate a new session.",
        }
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_margins(segment: Optional[str] = "all") -> Dict[str, Any]:
    """
    Fetch account margin and available funds for trading.

    Args:
        segment: Optional margin segment filter ('all', 'equity', or 'commodity'). Default is 'all'.

    Returns:
        Dict containing available cash, live balance, utilised margin, and full breakdown.
    """
    try:
        kite = get_kite_client()
        raw_margins = kite.margins()

        def extract_segment_summary(data: Dict[str, Any]) -> Dict[str, Any]:
            avail = data.get("available", {})
            util = data.get("utilised", {})
            return {
                "available_cash": round(float(avail.get("cash", 0.0)), 2),
                "live_balance": round(float(avail.get("live_balance", 0.0)), 2),
                "opening_balance": round(float(avail.get("opening_balance", 0.0)), 2),
                "collateral": round(float(avail.get("collateral", 0.0)), 2),
                "used_margin": round(float(util.get("debits", 0.0)), 2),
                "span_margin": round(float(util.get("span", 0.0)), 2),
                "exposure_margin": round(float(util.get("exposure", 0.0)), 2),
            }

        seg_lower = (segment or "all").lower()
        if seg_lower == "equity":
            eq = raw_margins.get("equity", {})
            return {
                "status": "success",
                "segment": "equity",
                "summary": extract_segment_summary(eq),
                "details": eq,
            }
        elif seg_lower == "commodity":
            comm = raw_margins.get("commodity", {})
            return {
                "status": "success",
                "segment": "commodity",
                "summary": extract_segment_summary(comm),
                "details": comm,
            }
        else:
            eq = raw_margins.get("equity", {})
            comm = raw_margins.get("commodity", {})
            return {
                "status": "success",
                "segment": "all",
                "summary": {
                    "equity": extract_segment_summary(eq),
                    "commodity": extract_segment_summary(comm),
                },
                "details": raw_margins,
            }

    except kite_exceptions.TokenException:
        return {
            "status": "error",
            "error_type": "TokenExpired",
            "message": "Kite access token has expired or is invalid. Run 'python authenticate.py' to generate a new session.",
        }
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_quote(instruments: List[str]) -> Dict[str, Any]:
    """
    Fetch real-time quotes, LTP, and OHLC market data for specified instruments.

    Args:
        instruments: List of instrument identifiers (e.g. ['NSE:INFY', 'NSE:RELIANCE', 'BSE:SENSEX', 'NSE:NIFTY 50']).
                     If the exchange prefix is omitted, 'NSE:' is prepended by default.

    Returns:
        Dict containing real-time quote data for each requested instrument.
    """
    try:
        kite = get_kite_client()
        cleaned_instruments = []
        for inst in instruments:
            item = str(inst).strip().upper()
            if not item:
                continue
            if ":" not in item:
                item = f"NSE:{item}"
            cleaned_instruments.append(item)

        if not cleaned_instruments:
            return {
                "status": "error",
                "message": "No valid instrument symbols provided. Example: ['NSE:INFY', 'NSE:TCS']",
            }

        quotes = kite.quote(cleaned_instruments)
        return {"status": "success", "count": len(quotes), "quotes": quotes}

    except kite_exceptions.TokenException:
        return {
            "status": "error",
            "error_type": "TokenExpired",
            "message": "Kite access token has expired or is invalid. Run 'python authenticate.py' to generate a new session.",
        }
    except kite_exceptions.PermissionException:
        return {
            "status": "error",
            "error_type": "PermissionRequired",
            "message": "Live market quotes require a Zerodha Kite 'Connect' subscription. Your app is currently on the free 'Personal' tier (which fully supports get_holdings, get_positions, and get_margins).",
        }
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
