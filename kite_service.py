"""
Zerodha Kite Data Service Module
Handles direct interactions with KiteConnect API for holdings, mutual funds, positions, and margins.
"""

from typing import Any, Dict, List, Optional
from kiteconnect import KiteConnect
import kiteconnect.exceptions as kite_exceptions

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
            "KITE_API_KEY is not configured. "
            "Please add your API key in .env or Streamlit Secrets."
        )

    if not access_token:
        raise RuntimeError(
            "KITE_ACCESS_TOKEN is missing or expired. "
            "Please run morning authentication to generate today's access token."
        )

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite


def fetch_holdings() -> Dict[str, Any]:
    """Fetch equity and ETF demat holdings with portfolio totals."""
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


def fetch_mf_holdings() -> Dict[str, Any]:
    """Fetch Zerodha Coin Mutual Fund holdings and returns."""
    kite = get_kite_client()
    raw_mf = kite.mf_holdings()

    total_invested = 0.0
    current_value = 0.0
    total_pnl = 0.0

    formatted_mf = []
    for m in raw_mf:
        qty = float(m.get("quantity", 0.0))
        avg_price = float(m.get("average_price", 0.0))
        last_price = float(m.get("last_price", 0.0))
        pnl = float(m.get("pnl", 0.0))
        invested = qty * avg_price
        cur_val = qty * last_price

        total_invested += invested
        current_value += cur_val
        total_pnl += pnl

        formatted_mf.append({
            "folio": m.get("folio"),
            "fund": m.get("fund"),
            "tradingsymbol": m.get("tradingsymbol"),
            "quantity": round(qty, 3),
            "average_price": round(avg_price, 2),
            "last_price": round(last_price, 2),
            "last_price_date": m.get("last_price_date"),
            "invested_amount": round(invested, 2),
            "current_value": round(cur_val, 2),
            "pnl": round(pnl, 2),
            "pnl_percentage": round((pnl / invested * 100), 2) if invested > 0 else 0.0,
        })

    summary = {
        "total_funds_count": len(formatted_mf),
        "total_investment": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_percentage": round(
            (total_pnl / total_invested * 100) if total_invested > 0 else 0.0, 2
        ),
    }

    return {"status": "success", "summary": summary, "mf_holdings": formatted_mf}


def fetch_positions() -> Dict[str, Any]:
    """Fetch intraday and overnight open positions."""
    kite = get_kite_client()
    data = kite.positions()
    net = data.get("net", [])
    day = data.get("day", [])
    open_pos = [p for p in net if p.get("quantity", 0) != 0]

    return {
        "status": "success",
        "summary": {
            "total_net_positions": len(net),
            "open_positions_count": len(open_pos),
            "total_unrealised_pnl": round(sum(float(p.get("unrealised", 0.0)) for p in net), 2),
            "total_realised_pnl": round(sum(float(p.get("realised", 0.0)) for p in net), 2),
            "total_pnl": round(sum(float(p.get("pnl", 0.0)) for p in net), 2),
            "total_m2m": round(sum(float(p.get("m2m", 0.0)) for p in net), 2),
        },
        "open_positions": open_pos,
        "net_positions": net,
        "day_positions": day,
    }


def fetch_margins(segment: Optional[str] = "all") -> Dict[str, Any]:
    """Fetch cash and margin utilization."""
    kite = get_kite_client()
    raw = kite.margins()

    def parse_seg(data: Dict[str, Any]) -> Dict[str, Any]:
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
        eq = raw.get("equity", {})
        return {"status": "success", "segment": "equity", "summary": parse_seg(eq), "details": eq}
    elif seg_lower == "commodity":
        comm = raw.get("commodity", {})
        return {"status": "success", "segment": "commodity", "summary": parse_seg(comm), "details": comm}
    else:
        return {
            "status": "success",
            "segment": "all",
            "summary": {
                "equity": parse_seg(raw.get("equity", {})),
                "commodity": parse_seg(raw.get("commodity", {})),
            },
            "details": raw,
        }


def fetch_quote(instruments: List[str]) -> Dict[str, Any]:
    """Fetch real-time quotes."""
    kite = get_kite_client()
    cleaned = [f"NSE:{i.strip().upper()}" if ":" not in i.strip().upper() else i.strip().upper() for i in instruments if str(i).strip()]
    if not cleaned:
        return {"status": "error", "message": "No valid instrument symbols provided."}
    return {"status": "success", "count": len(cleaned), "quotes": kite.quote(cleaned)}
