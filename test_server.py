#!/usr/bin/env python3
"""
Verification and Unit Tests for Zerodha Kite MCP Server
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from kite_mcp import get_holdings, get_margins, get_mf_holdings, get_positions, get_quote, mcp


class TestKiteMCPServer(unittest.TestCase):

    def test_registered_tools(self):
        """Verify that read-only tools including mutual funds are registered."""

        async def run_check():
            tools = await mcp.list_tools()
            tool_names = [t.name for t in tools]
            self.assertIn("get_holdings", tool_names)
            self.assertIn("get_mf_holdings", tool_names)
            self.assertIn("get_positions", tool_names)
            self.assertIn("get_margins", tool_names)
            self.assertIn("get_quote", tool_names)

            # Ensure NO order placement / trade execution tools exist
            for name in tool_names:
                self.assertNotIn("order", name.lower())
                self.assertNotIn("buy", name.lower())
                self.assertNotIn("sell", name.lower())
                self.assertNotIn("modify", name.lower())
                self.assertNotIn("cancel", name.lower())

        asyncio.run(run_check())

    @patch("kite_service.get_kite_client")
    def test_unauthenticated_graceful_handling(self, mock_get_client):
        """Verify graceful error reporting when credentials are missing or token has expired."""
        mock_get_client.side_effect = RuntimeError("KITE_ACCESS_TOKEN is missing")
        result = get_holdings()
        self.assertEqual(result["status"], "error")
        self.assertIn("missing", result["message"])

    @patch("kite_service.get_kite_client")
    def test_get_holdings_calculations(self, mock_get_client):
        """Verify calculation of total investment, value, and P&L in get_holdings."""
        mock_kite = MagicMock()
        mock_kite.holdings.return_value = [
            {
                "tradingsymbol": "INFY",
                "exchange": "NSE",
                "isin": "INE009A01021",
                "quantity": 10,
                "t1_quantity": 0,
                "average_price": 1500.0,
                "last_price": 1600.0,
                "close_price": 1590.0,
                "pnl": 1000.0,
                "day_change": 10.0,
                "day_change_percentage": 0.63,
            },
            {
                "tradingsymbol": "TCS",
                "exchange": "NSE",
                "isin": "INE467B01029",
                "quantity": 5,
                "t1_quantity": 0,
                "average_price": 3000.0,
                "last_price": 3200.0,
                "close_price": 3150.0,
                "pnl": 1000.0,
                "day_change": 50.0,
                "day_change_percentage": 1.59,
            },
        ]
        mock_get_client.return_value = mock_kite

        result = get_holdings()
        self.assertEqual(result["status"], "success")
        summary = result["summary"]
        self.assertEqual(summary["total_holdings_count"], 2)
        # Total investment: (10 * 1500) + (5 * 3000) = 15000 + 15000 = 30000
        self.assertEqual(summary["total_investment"], 30000.0)
        # Current value: (10 * 1600) + (5 * 3200) = 16000 + 16000 = 32000
        self.assertEqual(summary["current_value"], 32000.0)
        # Total PnL: 1000 + 1000 = 2000
        self.assertEqual(summary["total_pnl"], 2000.0)
        # PnL %: 2000 / 30000 * 100 = 6.67%
        self.assertEqual(summary["total_pnl_percentage"], 6.67)

    @patch("kite_service.get_kite_client")
    def test_get_mf_holdings(self, mock_get_client):
        """Verify mutual fund holdings formatting and total return calculation."""
        mock_kite = MagicMock()
        mock_kite.mf_holdings.return_value = [
            {
                "folio": "12345/67",
                "fund": "Nippon India Small Cap Fund",
                "tradingsymbol": "INF204K01W69",
                "quantity": 100.0,
                "average_price": 100.0,
                "last_price": 120.0,
                "pnl": 2000.0,
                "last_price_date": "2026-09-30",
            }
        ]
        mock_get_client.return_value = mock_kite

        result = get_mf_holdings()
        self.assertEqual(result["status"], "success")
        summary = result["summary"]
        self.assertEqual(summary["total_funds_count"], 1)
        self.assertEqual(summary["total_investment"], 10000.0)
        self.assertEqual(summary["current_value"], 12000.0)
        self.assertEqual(summary["total_pnl"], 2000.0)
        self.assertEqual(summary["total_pnl_percentage"], 20.0)

    @patch("kite_service.get_kite_client")
    def test_get_positions(self, mock_get_client):
        """Verify position filtering and totals in get_positions."""
        mock_kite = MagicMock()
        mock_kite.positions.return_value = {
            "net": [
                {
                    "tradingsymbol": "NIFTY24OCTFUT",
                    "exchange": "NFO",
                    "quantity": 50,
                    "average_price": 25000.0,
                    "last_price": 25100.0,
                    "unrealised": 5000.0,
                    "realised": 0.0,
                    "pnl": 5000.0,
                    "m2m": 5000.0,
                },
                {
                    "tradingsymbol": "BANKNIFTY24OCTFUT",
                    "exchange": "NFO",
                    "quantity": 0,  # Closed position
                    "average_price": 50000.0,
                    "last_price": 50200.0,
                    "unrealised": 0.0,
                    "realised": 3000.0,
                    "pnl": 3000.0,
                    "m2m": 0.0,
                },
            ],
            "day": [],
        }
        mock_get_client.return_value = mock_kite

        result = get_positions()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["total_net_positions"], 2)
        self.assertEqual(result["summary"]["open_positions_count"], 1)
        self.assertEqual(result["summary"]["total_unrealised_pnl"], 5000.0)
        self.assertEqual(result["summary"]["total_realised_pnl"], 3000.0)
        self.assertEqual(len(result["open_positions"]), 1)
        self.assertEqual(result["open_positions"][0]["tradingsymbol"], "NIFTY24OCTFUT")

    @patch("kite_service.get_kite_client")
    def test_get_margins(self, mock_get_client):
        """Verify get_margins summary extraction."""
        mock_kite = MagicMock()
        mock_kite.margins.return_value = {
            "equity": {
                "available": {"cash": 150000.0, "live_balance": 140000.0, "opening_balance": 150000.0, "collateral": 0.0},
                "utilised": {"debits": 10000.0, "span": 6000.0, "exposure": 4000.0},
            },
            "commodity": {
                "available": {"cash": 50000.0, "live_balance": 50000.0, "opening_balance": 50000.0, "collateral": 0.0},
                "utilised": {"debits": 0.0, "span": 0.0, "exposure": 0.0},
            },
        }
        mock_get_client.return_value = mock_kite

        result = get_margins("equity")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["segment"], "equity")
        self.assertEqual(result["summary"]["available_cash"], 150000.0)
        self.assertEqual(result["summary"]["used_margin"], 10000.0)

    @patch("kite_service.get_kite_client")
    def test_get_quote(self, mock_get_client):
        """Verify get_quote symbol formatting and quote retrieval."""
        mock_kite = MagicMock()
        mock_kite.quote.return_value = {
            "NSE:INFY": {
                "instrument_token": 408065,
                "last_price": 1600.0,
                "ohlc": {"open": 1595.0, "high": 1610.0, "low": 1590.0, "close": 1590.0},
                "volume": 2500000,
            }
        }
        mock_get_client.return_value = mock_kite

        # Test passing symbol without exchange prefix (should auto-prefix NSE:)
        result = get_quote(["INFY"])
        self.assertEqual(result["status"], "success")
        mock_kite.quote.assert_called_with(["NSE:INFY"])
        self.assertIn("NSE:INFY", result["quotes"])

    def test_stdio_jsonrpc_handshake(self):
        """Verify real MCP subprocess communication via stdio JSON-RPC handshake."""
        import json
        import subprocess
        import sys

        proc = subprocess.Popen(
            [sys.executable, "kite_mcp.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        try:
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            }
            proc.stdin.write(json.dumps(init_req) + "\n")
            proc.stdin.flush()

            init_line = proc.stdout.readline()
            init_res = json.loads(init_line)
            self.assertEqual(init_res.get("id"), 1)
            self.assertIn("serverInfo", init_res.get("result", {}))

            # Send initialized notification
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
            proc.stdin.flush()

            # Request tools list
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n")
            proc.stdin.flush()

            tools_line = proc.stdout.readline()
            tools_res = json.loads(tools_line)
            tools = tools_res.get("result", {}).get("tools", [])
            tool_names = [t["name"] for t in tools]

            self.assertEqual(len(tools), 5)
            self.assertIn("get_holdings", tool_names)
            self.assertIn("get_mf_holdings", tool_names)
            self.assertIn("get_positions", tool_names)
            self.assertIn("get_margins", tool_names)
            self.assertIn("get_quote", tool_names)
        finally:
            if proc.stdin:
                proc.stdin.close()
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()
            proc.terminate()
            proc.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
