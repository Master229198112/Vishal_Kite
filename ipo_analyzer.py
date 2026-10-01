#!/usr/bin/env python3
"""
IPO Analysis & Synthesis Engine
Computes multi-factor quantitative scorecards and integrates Google Gemini
(free-tier via Google AI Studio) for executive research summaries and investment verdicts.
"""

import os
from typing import Any, Dict, Optional
from dotenv import find_dotenv, load_dotenv

# Try importing google-genai
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def calculate_scorecard(gmp_data: Dict[str, Any], sub_data: Dict[str, Any], fund_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a quantitative 1-10 scorecard based on GMP, subscription demand,
    and fundamental structure.
    """
    gmp_pct = float(gmp_data.get("expected_listing_gain_pct", 0.0))
    sub_str = sub_data.get("total_subscription", "0x")
    sub_mult = float(sub_str.replace("x", "").strip()) if "x" in sub_str else 0.0

    # 1. GMP Score (0 to 10)
    if gmp_pct >= 50.0:
        gmp_score = 9.5
    elif gmp_pct >= 25.0:
        gmp_score = 8.0
    elif gmp_pct >= 15.0:
        gmp_score = 6.5
    elif gmp_pct >= 5.0:
        gmp_score = 5.0
    elif gmp_pct > 0.0:
        gmp_score = 4.0
    else:
        gmp_score = 2.0

    # 2. Subscription Score (0 to 10)
    if sub_mult >= 50.0:
        sub_score = 9.5
    elif sub_mult >= 20.0:
        sub_score = 8.5
    elif sub_mult >= 5.0:
        sub_score = 7.0
    elif sub_mult >= 1.0:
        sub_score = 5.5
    else:
        sub_score = 3.5

    # 3. Fundamental / Structural Score (0 to 10)
    is_mainboard = fund_data.get("category", "") == "Mainboard"
    fund_score = 7.5 if is_mainboard else 6.0

    # Weighted Overall Score: 40% GMP, 35% Demand, 25% Fundamentals
    overall_score = round((gmp_score * 0.40) + (sub_score * 0.35) + (fund_score * 0.25), 1)

    # Determine Verdict
    if overall_score >= 8.0:
        verdict = "STRONG APPLY (High Listing Gain & Strong Momentum)"
        listing_gain_potential = "High (> 25%)"
    elif overall_score >= 6.5:
        verdict = "APPLY (Good Listing Gain Potential with Moderate Risk)"
        listing_gain_potential = "Moderate (10% - 25%)"
    elif overall_score >= 5.0:
        verdict = "MAY APPLY / WAIT & WATCH (High Risk / Low Margin of Safety)"
        listing_gain_potential = "Low (< 10%)"
    else:
        verdict = "AVOID (Subdued GMP or Low Subscription Interest)"
        listing_gain_potential = "Flat / Negative"

    return {
        "overall_score": overall_score,
        "gmp_score": gmp_score,
        "subscription_score": sub_score,
        "fundamental_score": fund_score,
        "quantitative_verdict": verdict,
        "listing_gain_potential": listing_gain_potential,
        "risk_level": "High" if not is_mainboard else ("Moderate" if overall_score >= 6.5 else "Elevated"),
    }


from config import get_config


def generate_gemini_summary(company_name: str, payload: Dict[str, Any], language: str = "English") -> tuple[Optional[str], Optional[str]]:
    """
    Invoke Google Gemini to write a structured research memo in the requested language.
    Returns (narrative, model_name) or (None, None).
    """
    api_key = get_config("GEMINI_API_KEY")

    if not api_key or not GENAI_AVAILABLE:
        return None, None

    try:
        client = genai.Client(api_key=api_key)

        lang_instruction = ""
        if language and language.strip().lower() != "english":
            lang_instruction = (
                f"\nCRITICAL LANGUAGE REQUIREMENT: Write the entire analysis, section headings, "
                f"bullet points, and final verdict in {language}. "
                f"Ensure the language is fluent, professional, and natural for native {language} speakers, "
                f"while preserving financial numbers, symbols (₹), and percentages.\n"
            )

        prompt = f"""You are a senior institutional equity research analyst specializing in Indian IPOs.
Analyze the following compiled data for '{company_name}' and provide a clear, high-conviction research report.
{lang_instruction}
DATA CONTEXT:
- Company: {company_name}
- Category: {payload.get('fundamentals', {}).get('category', 'Mainboard')}
- Price Band: {payload.get('gmp', {}).get('issue_price', 'N/A')}
- Current GMP: Rs. {payload.get('gmp', {}).get('gmp_rs', 'N/A')} ({payload.get('gmp', {}).get('expected_listing_gain_pct', 'N/A')}%)
- Estimated Listing Price: Rs. {payload.get('gmp', {}).get('estimated_listing_price', 'N/A')}
- Subscription Multiple: {payload.get('subscription', {}).get('total_subscription', 'N/A')}
- Quantitative Score: {payload.get('scorecard', {}).get('overall_score', 'N/A')} / 10
- Quantitative Verdict: {payload.get('scorecard', {}).get('quantitative_verdict', 'N/A')}

STRUCTURE YOUR RESPONSE IN GITHUB MARKDOWN AS FOLLOWS:
### 1. Executive Summary & Verdict
State the clear recommendation (APPLY FOR LISTING GAINS / APPLY FOR LONG TERM / AVOID) with rationale.

### 2. Grey Market & Demand Sentiment
Assess what the GMP and subscription numbers indicate about institutional and retail appetite.

### 3. Key Strengths & Catalysts
Bullet points on growth levers and positives.

### 4. Key Risks & Red Flags
Valuation concerns, promoter dilution (OFS), sector headwinds, or SME liquidity risks.

### 5. Strategy for Retail & HNI Investors
Exact bidding strategy: cut-off price, listing-day exit vs holding for multi-bagger gains.
"""

        # Candidate models with automatic fallback
        candidate_models = ["gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text, model_name
            except Exception as model_err:
                print(f"[Info] Model {model_name} failed ({model_err}), trying next candidate...")

        return None, None

    except Exception as exc:
        print(f"[Warning] Gemini API call failed: {exc}")
        return None, None


def generate_full_ipo_analysis(
    company_name: str,
    gmp_data: Dict[str, Any],
    sub_data: Dict[str, Any],
    fund_data: Dict[str, Any],
    media_data: Dict[str, Any],
    language: str = "English",
) -> Dict[str, Any]:
    """Synthesize all research vectors into an executive analysis package."""
    scorecard = calculate_scorecard(gmp_data, sub_data, fund_data)

    payload = {
        "company_name": company_name,
        "scorecard": scorecard,
        "gmp": gmp_data,
        "subscription": sub_data,
        "fundamentals": fund_data,
        "media": media_data,
        "language": language,
    }

    ai_narrative, used_model = generate_gemini_summary(company_name, payload, language=language)

    return {
        "status": "success",
        "company_name": company_name,
        "scorecard": scorecard,
        "ai_narrative_report": ai_narrative or (
            "Rule-Based Summary: "
            f"Overall score is {scorecard['overall_score']}/10 with verdict '{scorecard['quantitative_verdict']}'. "
            f"Expected listing gain is {scorecard['listing_gain_potential']}. "
            "\n\n[Tip: Configure GEMINI_API_KEY in your .env file to enable automated Gemini deep-dive narrative reports!]"
        ),
        "ai_powered_by": f"Google Gemini ({used_model})" if ai_narrative else "Rule-Based Engine",
        "gmp_summary": gmp_data,
        "subscription_summary": sub_data,
        "top_analyst_videos": media_data.get("videos", [])[:3],
    }


if __name__ == "__main__":
    print("Testing calculate_scorecard()...")
    dummy_gmp = {"expected_listing_gain_pct": 35.0, "issue_price": 500, "gmp_rs": 175}
    dummy_sub = {"total_subscription": "24.5x"}
    dummy_fund = {"category": "Mainboard"}
    sc = calculate_scorecard(dummy_gmp, dummy_sub, dummy_fund)
    print("Scorecard:", sc)
