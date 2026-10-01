#!/usr/bin/env python3
"""
Unit and Integration Tests for IPO Research MCP Server
"""

import asyncio
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from ipo_analyzer import calculate_scorecard
from ipo_fetcher import _safe_float
from ipo_mcp import mcp


class TestIPOMCPServer(unittest.TestCase):

    def test_registered_tools(self):
        """Verify that all 6 IPO research tools are registered."""

        async def run_check():
            tools = await mcp.list_tools()
            tool_names = [t.name for t in tools]
            expected_tools = [
                "get_upcoming_ipos",
                "get_ipo_gmp",
                "get_ipo_subscription",
                "get_ipo_fundamentals",
                "get_ipo_media",
                "get_ipo_analysis_summary",
            ]
            for tool in expected_tools:
                self.assertIn(tool, tool_names)

        asyncio.run(run_check())

    def test_safe_float_parser(self):
        """Verify float parser handles currency, commas, and edge cases."""
        self.assertEqual(_safe_float("1,234.50"), 1234.5)
        self.assertEqual(_safe_float("Rs. 500"), 500.0)
        self.assertEqual(_safe_float("invalid", default=10.0), 10.0)

    def test_scorecard_calculation(self):
        """Verify multi-factor weighting and verdict thresholds."""
        # Strong IPO (high GMP, high subscription)
        strong_gmp = {"expected_listing_gain_pct": 60.0}
        strong_sub = {"total_subscription": "45.0x"}
        strong_fund = {"category": "Mainboard"}

        scorecard = calculate_scorecard(strong_gmp, strong_sub, strong_fund)
        self.assertGreaterEqual(scorecard["overall_score"], 8.0)
        self.assertIn("STRONG APPLY", scorecard["quantitative_verdict"])

        # Weak IPO (low GMP, low subscription)
        weak_gmp = {"expected_listing_gain_pct": 2.0}
        weak_sub = {"total_subscription": "0.5x"}
        weak_fund = {"category": "SME"}

        weak_scorecard = calculate_scorecard(weak_gmp, weak_sub, weak_fund)
        self.assertLess(weak_scorecard["overall_score"], 5.0)
        self.assertIn("AVOID", weak_scorecard["quantitative_verdict"])

    def test_stdio_jsonrpc_handshake(self):
        """Verify real MCP subprocess communication via stdio JSON-RPC handshake."""
        proc = subprocess.Popen(
            [sys.executable, "ipo_mcp.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        try:
            # 1. Initialize Request
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-ipo-client", "version": "1.0.0"},
                },
            }
            proc.stdin.write(json.dumps(init_req) + "\n")
            proc.stdin.flush()

            init_line = proc.stdout.readline()
            init_res = json.loads(init_line)
            self.assertEqual(init_res.get("id"), 1)
            self.assertEqual(init_res.get("result", {}).get("serverInfo", {}).get("name"), "ipo-research")

            # 2. Initialized Notification
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
            proc.stdin.flush()

            # 3. Request tools/list
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n")
            proc.stdin.flush()

            tools_line = proc.stdout.readline()
            tools_res = json.loads(tools_line)
            tools = tools_res.get("result", {}).get("tools", [])
            tool_names = [t["name"] for t in tools]

            self.assertEqual(len(tools), 6)
            self.assertIn("get_upcoming_ipos", tool_names)
            self.assertIn("get_ipo_gmp", tool_names)
            self.assertIn("get_ipo_subscription", tool_names)
            self.assertIn("get_ipo_fundamentals", tool_names)
            self.assertIn("get_ipo_media", tool_names)
            self.assertIn("get_ipo_analysis_summary", tool_names)

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
