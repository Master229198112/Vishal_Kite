"""
Unit tests for new features:
- Allotment Checker
- RFC 6238 TOTP Generator
- Morning Briefing & WhatsApp URL Generation
- Multi-Language AI Synthesis Interface
"""

import unittest
import base64
import allotment_checker
import totp_auth
import notifications
import ipo_mcp
import ipo_analyzer


class TestNewFeatures(unittest.TestCase):
    def test_pan_validation(self):
        self.assertTrue(allotment_checker.validate_pan("ABCDE1234F"))
        self.assertTrue(allotment_checker.validate_pan("abcde1234f"))
        self.assertFalse(allotment_checker.validate_pan("INVALID123"))
        self.assertFalse(allotment_checker.validate_pan("12345ABCDE"))
        self.assertFalse(allotment_checker.validate_pan(""))

    def test_allotment_registrars_catalog(self):
        regs = allotment_checker.get_all_registrars()
        self.assertIn("link_intime", regs)
        self.assertIn("kfintech", regs)
        self.assertIn("bigshare", regs)
        self.assertTrue(regs["link_intime"]["url"].startswith("http"))

    def test_totp_generation(self):
        # Base32 secret for '12345678901234567890'
        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        code = totp_auth.generate_totp(secret)
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_morning_briefing_generation(self):
        briefing = notifications.generate_morning_briefing(include_demat=False)
        self.assertIn("Vishal TradeX Morning", briefing)
        self.assertIn("Top Tracked IPOs", briefing)

        wa_url = notifications.get_whatsapp_share_url(briefing)
        self.assertTrue(wa_url.startswith("https://api.whatsapp.com/send?text="))

    def test_multi_language_summary_interface(self):
        dummy_gmp = {"expected_listing_gain_pct": 30.0, "issue_price": 100, "gmp_rs": 30}
        dummy_sub = {"total_subscription": "15.0x"}
        dummy_fund = {"category": "Mainboard"}
        dummy_media = {"videos": []}

        # Should accept language parameter without error
        res = ipo_analyzer.generate_full_ipo_analysis(
            "Test Company",
            dummy_gmp,
            dummy_sub,
            dummy_fund,
            dummy_media,
            language="Hindi (हिंदी)",
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("ai_narrative_report", res)

    def test_get_assigned_registrar_for_ipo(self):
        reg_tna = allotment_checker.get_assigned_registrar_for_ipo("TNA Solutions")
        self.assertIn("maashitla", reg_tna["name"].lower())

        reg_acme = allotment_checker.get_assigned_registrar_for_ipo("Acme India Industries")
        self.assertIn("bigshare", reg_acme["name"].lower())

        reg_shah = allotment_checker.get_assigned_registrar_for_ipo("Shah Investor's Home")
        self.assertIn("link intime", reg_shah["name"].lower())


if __name__ == "__main__":
    unittest.main()
