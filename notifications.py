"""
Morning Briefing & Notification Service Module
Generates automated daily IPO and portfolio intelligence briefings
and dispatches them via Telegram Bot API or WhatsApp.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote_plus
import httpx

from config import get_config
import ipo_mcp
import kite_mcp


def generate_morning_briefing(include_demat: bool = True) -> str:
    """Format an executive morning intelligence briefing message."""
    today_str = datetime.now().strftime("%A, %d %b %Y")

    lines = [
        "🌅 *Vishal TradeX Morning Market & IPO Briefing*",
        f"📅 *Date:* {today_str}",
        "",
    ]

    # 1. Demat Portfolio Summary
    if include_demat:
        try:
            m_res = kite_mcp.get_margins()
            h_res = kite_mcp.get_holdings()
            mf_res = kite_mcp.get_mf_holdings()

            cash = m_res.get("summary", {}).get("equity", {}).get("available_cash", 0.0)
            eq_val = h_res.get("summary", {}).get("current_value", 0.0)
            eq_pnl_pct = h_res.get("summary", {}).get("total_pnl_percentage", 0.0)
            mf_val = mf_res.get("summary", {}).get("current_value", 0.0)
            mf_pnl_pct = mf_res.get("summary", {}).get("total_pnl_percentage", 0.0)
            net_worth = cash + eq_val + mf_val

            lines.extend([
                "📊 *Zerodha Demat Portfolio:*",
                f"• *Net Worth:* ₹{net_worth:,.2f}",
                f"• *Equities Value:* ₹{eq_val:,.2f} ({eq_pnl_pct:+.2f}%)",
                f"• *Mutual Funds:* ₹{mf_val:,.2f} ({mf_pnl_pct:+.2f}%)",
                f"• *Available Cash Margin:* ₹{cash:,.2f}",
                "",
            ])
        except Exception:
            pass

    # 2. Top Live IPOs & GMP Market
    try:
        ipo_data = ipo_mcp.get_upcoming_ipos()
        ipos = ipo_data.get("ipos", [])
        live_ipos = [i for i in ipos if i.get("status") in ["Open", "Upcoming"]]
        # Sort by expected gain descending
        live_ipos.sort(key=lambda x: x.get("gmp_percentage", 0.0), reverse=True)

        lines.append("🔥 *Top Tracked IPOs & Grey Market Premium:*")
        for idx, ipo in enumerate(live_ipos[:5], 1):
            name = ipo.get("company_name", "")
            cat = ipo.get("type", "Mainboard")
            gmp_rs = ipo.get("gmp_in_rs", 0.0)
            gmp_pct = ipo.get("gmp_percentage", 0.0)
            sub = ipo.get("subscription_multiple", 0.0)
            status = ipo.get("status", "Open")

            lines.append(
                f"{idx}. *{name}* ({cat} - {status})\n"
                f"   • GMP: ₹{gmp_rs:,.1f} ({gmp_pct:+.1f}% gain) | Sub: {sub:.2f}x"
            )
        lines.append("")
    except Exception:
        pass

    lines.extend([
        "⚡ *Market Note:* Indian market opens 9:15 AM IST.",
        "🌐 *Terminal:* https://vishal-kite.streamlit.app",
    ])

    return "\n".join(lines)


def send_telegram_briefing(
    message: Optional[str] = None,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """Dispatch morning briefing via Telegram Bot API."""
    token = bot_token or get_config("TELEGRAM_BOT_TOKEN")
    cid = chat_id or get_config("TELEGRAM_CHAT_ID")

    if not token or not cid:
        return False, "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured."

    text = message or generate_morning_briefing(include_demat=True)
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        resp = httpx.post(
            api_url,
            json={"chat_id": cid, "text": text, "parse_mode": "Markdown"},
            timeout=10.0,
        )
        if resp.status_code == 200 and resp.json().get("ok"):
            return True, "Morning briefing successfully delivered to Telegram!"
        return False, f"Telegram API error: {resp.text}"
    except Exception as exc:
        return False, f"Telegram connection error: {str(exc)}"


def get_whatsapp_share_url(message: Optional[str] = None) -> str:
    """Generate universal 1-click WhatsApp share link for the briefing."""
    text = message or generate_morning_briefing(include_demat=False)
    encoded = quote_plus(text)
    return f"https://api.whatsapp.com/send?text={encoded}"
