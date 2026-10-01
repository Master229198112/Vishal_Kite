# Vishal TradeX — Kite & IPO Intelligence Suite

A dual Model Context Protocol (MCP) server suite providing:
1. **Zerodha Kite:** Read-only portfolio analytics, position tracking, and market monitoring.
2. **IPO Research & Intelligence:** Real-time Grey Market Premium (GMP), fundamentals, subscription demand, YouTube video reviews, and automated AI research reports powered by Google Gemini.

## Architecture & Safeguards

- **Strictly Read-Only:** Exposes only research, analytics, and data extraction tools. Order placement and modification APIs are omitted.
- **Modular Multi-Server Setup:** Registered side-by-side in `.agents/mcp_config.json`.
- **Public 24/7 IPO Research:** IPO research requires zero login credentials and works on market holidays and weekends.
- **AI Executive Synthesis:** Integrates Google Gemini (`gemini-2.5-flash`) via free Google AI Studio keys for institutional research summaries.

## Project Structure

```
d:/VS_Code/Vishal_Kite/
├── .agents/
│   └── mcp_config.json      # Antigravity MCP multi-server registry
├── .env.example              # Template for API credentials
├── .gitignore                # Excludes .env and cache artifacts
├── requirements.txt          # Python dependencies
├── authenticate.py           # Daily token generator for Kite
├── kite_mcp.py               # Kite MCP server (portfolio & market data)
├── ipo_fetcher.py            # Live GMP, subscription, and fundamentals scraper
├── ipo_media.py              # YouTube video search & analyst reviews
├── ipo_analyzer.py           # Multi-factor scorecard & Gemini AI synthesis
├── ipo_mcp.py                # IPO Research MCP server
├── test_server.py            # Kite MCP test suite
└── test_ipo_mcp.py           # IPO Research MCP test suite
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
- Add `KITE_API_KEY` and `KITE_API_SECRET` for Zerodha Kite.
- (Optional, Recommended): Add `GEMINI_API_KEY` (Free from [Google AI Studio](https://aistudio.google.com/)) to enable AI-written executive IPO research reports.

### 3. Run Tests & Verification
Verify both MCP servers and stdio handshakes:
```bash
python -m unittest test_server.py
python -m unittest test_ipo_mcp.py
```

### 4. Launch the Interactive Dashboard
Launch the full-featured web terminal:
```bash
streamlit run dashboard.py
```
Open your browser at **`http://localhost:8501`** to track your portfolio, explore live IPOs with Gemini AI, and perform 1-click morning authentication.

## Available MCP Tools

### 1. Zerodha Kite Server (`zerodha-kite`)
| Tool | Description |
| :--- | :--- |
| `get_holdings` | Portfolio equity & ETF holdings with buy price, LTP, P&L, and valuation summary. |
| `get_positions` | Open intraday and overnight positions with unrealised/realised P&L and M2M metrics. |
| `get_margins` | Cash balance and margin utilization for `all`, `equity`, or `commodity` segments. |
| `get_quote` | Real-time quotes, LTP, and OHLC data for specified symbols. |

### 2. IPO Research Server (`ipo-research`)
| Tool | Description |
| :--- | :--- |
| `get_upcoming_ipos` | Active, upcoming, and recently listed Mainboard & SME IPOs. |
| `get_ipo_gmp` | Live Grey Market Premium (₹), estimated listing price, and percentage gain. |
| `get_ipo_subscription` | Real-time bidding demand multiples (Retail, NII/HNI, QIB, Total). |
| `get_ipo_fundamentals` | Issue size, lot size, min retail investment, Fresh vs OFS, and dates. |
| `get_ipo_media` | Top YouTube reviews, analyst coverage, and promoter interviews. |
| `get_ipo_analysis_summary` | Full synthesis: 1-10 scorecard, risk evaluation, and Gemini AI executive verdict. |
