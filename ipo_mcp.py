#!/usr/bin/env python3
"""
IPO Intelligence & Research MCP Server
Model Context Protocol (MCP) server providing comprehensive read-only IPO analytics:
- get_upcoming_ipos: Active & upcoming Mainboard and SME IPO listings.
- get_ipo_gmp: Real-time Grey Market Premium (GMP) and estimated listing gains.
- get_ipo_subscription: Live bidding demand across QIB, NII, and Retail.
- get_ipo_fundamentals: Valuation, issue size, lot size, and structure.
- get_ipo_media: Top YouTube video reviews and analyst commentary.
- get_ipo_analysis_summary: AI-powered research memo and investment scorecard (via Google Gemini).

SAFEGUARDS:
This server is strictly read-only. It provides intelligence, analytics, and research.
"""

from typing import Any, Dict, Optional
from ipo_analyzer import generate_full_ipo_analysis
from ipo_fetcher import (
    fetch_ipo_fundamentals,
    fetch_ipo_gmp,
    fetch_ipo_subscription,
    fetch_upcoming_ipos,
)
from ipo_media import fetch_ipo_videos

try:
    from mcp.server.mcpserver import MCPServer
except (ImportError, ModuleNotFoundError):
    from mcp.server.fastmcp import FastMCP as MCPServer

# Initialize IPO Research MCP server
mcp = MCPServer(
    "ipo-research",
    description="IPO research, Grey Market Premium (GMP), fundamentals, YouTube reviews, and AI synthesis server",
)


@mcp.tool()
def get_upcoming_ipos() -> Dict[str, Any]:
    """
    Fetch all active, upcoming, and recently listed IPOs (Mainboard & SME).

    Returns:
        Dict containing total count and list of IPOs with company name, category,
        price band, lot size, issue dates, GMP in Rs, and subscription multiple.
    """
    try:
        ipos = fetch_upcoming_ipos()
        return {
            "status": "success",
            "count": len(ipos),
            "ipos": ipos,
        }
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_ipo_gmp(symbol_or_name: str) -> Dict[str, Any]:
    """
    Fetch real-time Grey Market Premium (GMP) and estimated listing gains for an IPO.

    Args:
        symbol_or_name: Company name or trading symbol (e.g. 'Tata Tech', 'Acme India').

    Returns:
        Dict containing current GMP (Rs), expected listing price, percentage gain,
        and trend sentiment.
    """
    try:
        return fetch_ipo_gmp(symbol_or_name)
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_ipo_subscription(symbol_or_name: str) -> Dict[str, Any]:
    """
    Fetch live bidding subscription multiples for an IPO.

    Args:
        symbol_or_name: Company name or trading symbol.

    Returns:
        Dict containing total subscription multiple and category breakdowns (Retail, NII/HNI, QIB).
    """
    try:
        return fetch_ipo_subscription(symbol_or_name)
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_ipo_fundamentals(symbol_or_name: str) -> Dict[str, Any]:
    """
    Fetch fundamental details, issue size, lot size, and structure for an IPO.

    Args:
        symbol_or_name: Company name or trading symbol.

    Returns:
        Dict containing issue size (Cr), price band, lot size, min retail investment,
        and issue structure.
    """
    try:
        return fetch_ipo_fundamentals(symbol_or_name)
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_ipo_media(symbol_or_name: str, max_results: Optional[int] = 5) -> Dict[str, Any]:
    """
    Search and retrieve top YouTube video reviews, analyst breakdowns, and promoter interviews.

    Args:
        symbol_or_name: Company name or trading symbol.
        max_results: Number of video results to return (default: 5).

    Returns:
        Dict containing video titles, channel names, watch links, and views.
    """
    try:
        return fetch_ipo_videos(symbol_or_name, max_results=max_results or 5)
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def get_ipo_analysis_summary(symbol_or_name: str, language: Optional[str] = "English") -> Dict[str, Any]:
    """
    Generate a comprehensive executive research report and investment verdict for an IPO.
    Synthesizes GMP, bidding subscription, fundamentals, and analyst videos.
    Integrates Google Gemini (via free GEMINI_API_KEY in .env) for institutional-grade narrative analysis.

    Args:
        symbol_or_name: Company name or trading symbol.
        language: Desired output language for the research memo (e.g. English, Hindi, Marathi, etc.).

    Returns:
        Dict containing quantitative scorecard (1-10), listing gain potential, risk level,
        executive recommendation, and top analyst video links.
    """
    try:
        gmp_data = fetch_ipo_gmp(symbol_or_name)
        if gmp_data.get("status") == "error":
            return gmp_data

        sub_data = fetch_ipo_subscription(symbol_or_name)
        fund_data = fetch_ipo_fundamentals(symbol_or_name)
        media_data = fetch_ipo_videos(symbol_or_name, max_results=3)

        return generate_full_ipo_analysis(
            symbol_or_name,
            gmp_data,
            sub_data,
            fund_data,
            media_data,
            language=language or "English",
        )
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
