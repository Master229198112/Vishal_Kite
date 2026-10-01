#!/usr/bin/env python3
"""
Zerodha Kite MCP Server
Model Context Protocol (MCP) server providing read-only tools for Zerodha Kite:
- get_holdings: Portfolio equity/ETF holdings with buy price, LTP, P&L.
- get_mf_holdings: Zerodha Coin mutual fund holdings and returns.
- get_positions: Open intraday & overnight positions.
- get_margins: Available cash and margin usage for equity & commodity.
- get_quote: Real-time LTP and OHLC market quotes.

SAFEGUARD:
This server is STRICTLY READ-ONLY. No order execution or modification tools are exposed.
"""

from typing import Any, Dict, List, Optional
import kiteconnect.exceptions as kite_exceptions
from kite_service import (
    fetch_holdings,
    fetch_margins,
    fetch_mf_holdings,
    fetch_positions,
    fetch_quote,
    get_kite_client,
)

try:
    from mcp.server.mcpserver import MCPServer
except (ImportError, ModuleNotFoundError):
    from mcp.server.fastmcp import FastMCP as MCPServer

# Initialize MCP server
mcp = MCPServer(
    "zerodha-kite",
    description="Zerodha Kite read-only portfolio analytics, mutual funds, and market monitoring server",
)


def _handle_kite_error(exc: Exception) -> Dict[str, Any]:
    """Helper to structure clean Kite exceptions."""
    if isinstance(exc, kite_exceptions.TokenException):
        return {
            "status": "error",
            "error_type": "TokenExpired",
            "message": "Kite access token expired or invalid. Please refresh your daily session.",
        }
    if isinstance(exc, kite_exceptions.PermissionException):
        return {
            "status": "error",
            "error_type": "PermissionRequired",
            "message": "This API call requires a Kite Connect subscription (Personal tier supports holdings and margins).",
        }
    return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_holdings() -> Dict[str, Any]:
    """
    Fetch equity and ETF holdings from Zerodha Kite.
    Returns portfolio valuation, buy price, LTP, and P&L breakdown.
    """
    try:
        return fetch_holdings()
    except Exception as exc:
        return _handle_kite_error(exc)


@mcp.tool()
def get_mf_holdings() -> Dict[str, Any]:
    """
    Fetch Mutual Fund holdings and SIP investments from Zerodha Coin.
    Returns fund names, folio numbers, units, invested amount, current value, and P&L.
    """
    try:
        return fetch_mf_holdings()
    except Exception as exc:
        return _handle_kite_error(exc)


@mcp.tool()
def get_positions() -> Dict[str, Any]:
    """
    Fetch open intraday (MIS) and overnight (NRML) positions from Zerodha Kite.
    Returns open positions and realised/unrealised P&L metrics.
    """
    try:
        return fetch_positions()
    except Exception as exc:
        return _handle_kite_error(exc)


@mcp.tool()
def get_margins(segment: Optional[str] = "all") -> Dict[str, Any]:
    """
    Fetch account margin and available funds for trading.
    'segment' can be 'all', 'equity', or 'commodity'.
    """
    try:
        return fetch_margins(segment)
    except Exception as exc:
        return _handle_kite_error(exc)


@mcp.tool()
def get_quote(instruments: List[str]) -> Dict[str, Any]:
    """
    Fetch real-time quotes, LTP, and OHLC market data for specified instruments.
    """
    try:
        return fetch_quote(instruments)
    except Exception as exc:
        return _handle_kite_error(exc)


if __name__ == "__main__":
    mcp.run(transport="stdio")
