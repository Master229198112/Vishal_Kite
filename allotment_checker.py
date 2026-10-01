"""
IPO Allotment Checker & Registrar Integration Module
Provides 1-click direct portal routing, registrar lookup, and allotment lifecycle tracking
for Link Intime, KFintech, Bigshare, Skyline, Maashitla, Cameo, and BSE/NSE.
"""

import re
from typing import Any, Dict, List, Optional

REGISTRARS = {
    "link_intime": {
        "name": "Link Intime India Pvt Ltd",
        "url": "https://linkintime.co.in/initial_offer/public-issues.html",
        "alt_url": "https://web.linkintime.co.in/client-downloads/IPO_allotment.html",
        "supported_searches": ["PAN Number", "Application Number", "DP/Client ID", "Account No"],
        "description": "Primary registrar for large Mainboard issues (Tata, Bajaj, Hyundai, etc.).",
    },
    "kfintech": {
        "name": "KFin Technologies Ltd (KFintech)",
        "url": "https://ris.kfintech.com/ipostatus/",
        "alt_url": "https://kosmic.kfintech.com/ipostatus/",
        "supported_searches": ["PAN Number", "Application Number", "DP/Client ID"],
        "description": "Major registrar for top Mainboard and select SME issues.",
    },
    "bigshare": {
        "name": "Bigshare Services Pvt Ltd",
        "url": "https://ipo.bigshareonline.com/ipo_status.html",
        "alt_url": "https://www.bigshareonline.com/InvestorIPOStatus.html",
        "supported_searches": ["PAN Number", "Application Number", "Beneficiary ID"],
        "description": "Most prominent registrar for BSE & NSE SME IPO listings.",
    },
    "skyline": {
        "name": "Skyline Financial Services Pvt Ltd",
        "url": "https://www.skylinerta.com/ipo.php",
        "alt_url": "https://www.skylinerta.com/",
        "supported_searches": ["PAN Number", "Application Number", "DP ID"],
        "description": "Registrar for manufacturing & SME IPO offerings.",
    },
    "maashitla": {
        "name": "Maashitla Securities Pvt Ltd",
        "url": "https://maashitla.com/allotment-status/public-issues",
        "alt_url": "https://maashitla.com/",
        "supported_searches": ["PAN Number", "Application Number", "Demat Account"],
        "description": "Specialist registrar for emerging growth & SME enterprises.",
    },
    "cameo": {
        "name": "Cameo Corporate Services Ltd",
        "url": "https://ipo.cameoindia.com/",
        "alt_url": "https://www.cameoindia.com/",
        "supported_searches": ["PAN Number", "Folio / DP ID", "Application Number"],
        "description": "Registrar based in South India serving industrial & consumer IPOs.",
    },
    "bse_official": {
        "name": "BSE India Official Allotment Check",
        "url": "https://www.bseindia.com/investors/appli_check.aspx",
        "alt_url": "https://www.bseindia.com/",
        "supported_searches": ["Application Number + PAN Number"],
        "description": "Centralized exchange verification for all BSE listed issues.",
    },
}


def get_all_registrars() -> Dict[str, Dict[str, Any]]:
    """Return catalog of all supported IPO registrars."""
    return REGISTRARS


def validate_pan(pan: str) -> bool:
    """Validate 10-character standard Indian PAN format (ABCDE1234F)."""
    if not pan:
        return False
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan.strip().upper()))


def get_allotment_timeline(ipo_name: str, open_date: str, close_date: str) -> List[Dict[str, str]]:
    """Return standard SEBI T+3 IPO allotment and listing milestones."""
    return [
        {"step": "1. Bidding Window", "status": f"{open_date} to {close_date}", "icon": "📝"},
        {"step": "2. Basis of Allotment (BOA)", "status": "T+1 Business Day (Evening)", "icon": "⚖️"},
        {"step": "3. Refund Initiation / ASBA Unblock", "status": "T+2 Business Day (Morning)", "icon": "💸"},
        {"step": "4. Credit of Shares to Demat", "status": "T+2 Business Day (Evening)", "icon": "📥"},
        {"step": "5. Listing & Trading on Exchange", "status": "T+3 Business Day (9:15 AM IST)", "icon": "🔔"},
    ]


def format_search_summary(pan: str, app_no: Optional[str] = None) -> Dict[str, str]:
    """Format sanitized search parameters for verification."""
    clean_pan = pan.strip().upper() if pan else ""
    masked_pan = f"{clean_pan[:2]}*****{clean_pan[-2:]}" if len(clean_pan) == 10 else clean_pan
    return {
        "clean_pan": clean_pan,
        "masked_pan": masked_pan,
        "is_valid_pan": validate_pan(clean_pan),
        "application_no": app_no.strip() if app_no else "",
    }
