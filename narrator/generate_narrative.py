
import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NARRATOR_DIR = PROJECT_ROOT / "narrator"

FINDINGS_PATH = NARRATOR_DIR / "findings.json"
OUTPUT_PATH = NARRATOR_DIR / "sample_output.txt"

MODEL_NAME = "gemini-3.8-flash"
TIMEOUT_MS = 30000
MAX_OUTPUT_TOKENS = 1200

SYSTEM_INSTRUCTION = """
You are a careful data analyst writing a concise business findings report.

Rules:
1. Use only facts and figures provided in the input findings.
2. Never invent statistics, causes, or business explanations.
3. Preserve all important numbers and dates exactly.
4. Clearly state that the dataset is synthetic, not official Mamaearth data.
5. Distinguish association from causation.
6. Explain the impact of quantity outliers on monthly revenue.
7. Use professional, concise language with clear headings.
"""


def offline_fallback(findings):
    """Create a deterministic narrative without an API request."""

    rates = findings["payment_method_return_rates"]
    highest = max(rates, key=lambda item: item["return_rate_pct"])

    peak_with = findings["peak_month_including_outliers"]
    peak_without = findings["peak_month_excluding_outliers"]

    return f"""
MAMAEARTH GROWTH ANALYTICS — FINDINGS SUMMARY

DATA NOTE
{findings['data_note']}

DATA QUALITY
The raw dataset contained {findings['raw_order_count']} orders.
After removing {findings['duplicate_submissions_removed']} duplicate
submissions, {findings['cleaned_order_count']} orders remained.

REVENUE
Revenue from the cleaned orders was
₹{findings['cleaned_revenue_inr']:,.2f}.

RETURNS
{highest['payment_method']} had the highest observed return rate,
at {highest['return_rate_pct']:.2f}% across
{highest['total_orders']} orders. This is an association in the
dataset and does not establish causation.

MONTHLY REVENUE AND OUTLIERS
Including flagged quantity outliers, the peak month was
{peak_with['month']}, with revenue of
₹{peak_with['revenue_inr']:,.2f}.

Excluding flagged quantity outliers, the peak month was
{peak_without['month']}, with revenue of
₹{peak_without['revenue_inr']:,.2f}.

INTERPRETATION
Large-quantity orders can materially affect monthly revenue.
Both revenue views should be considered when interpreting trends.

These findings describe a synthetic educational dataset and must
not be presented as official Mamaearth business performance.
""".strip()


def normalize(text):
    """Normalize presentation differences without removing meaningful digits."""
    text = text.lower().replace("₹", "")
    return re.sub(r"[\s,]", "", text)


def check_accuracy(narrative, findings):
    """Check that key computed figures appear in the narrative."""

    text = normalize(narrative)

    highest_rate = max(
        findings["payment_method_return_rates"],
        key=lambda item: item["return_rate_pct"],
    )["return_rate_pct"]

    required_values = [
        str(findings["cleaned_order_count"]),
        str(findings["duplicate_submissions_removed"]),
        f"{findings['cleaned_revenue_inr']:,.2f}",
        f"{highest_rate:.2f}%",
        findings["peak_month_including_outliers"]["month"],
        findings["peak_month_excluding_outliers"]["month"],
    ]

    missing = [
        value for value in required_values
        if normalize(value) not in text
    ]

    return len(missing) == 0, missing


def generate_with_gemini(findings, api_key):
    """Generate a narrative using Gemini with a timeout."""

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )

    prompt = (
        "Write a concise business findings report using only this "
        "computed JSON. Preserve the following computed figures exactly: "
        f"{findings['cleaned_order_count']} cleaned orders, "
        f"{findings['duplicate_submissions_removed']} duplicate submissions, "
        f"revenue ₹{findings['cleaned_revenue_inr']:,.2f}, "
        f"peak months {findings['peak_month_including_outliers']['month']} "
        "including outliers and "
        f"{findings['peak_month_excluding_outliers']['month']} "
        "excluding outliers. Include the highest payment-method return "
        "rate and clearly label this dataset as synthetic, not official "
        "Mamaearth data.\n\n"
        + json.dumps(findings, indent=2, ensure_ascii=False)
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )

    if not response.text or not response.text.strip():
        raise ValueError("Gemini returned an empty narrative.")

    return response.text.strip()


def main():
    with open(FINDINGS_PATH, "r", encoding="utf-8") as file:
        findings = json.load(file)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    mode = "offline fallback"
    narrative = None

    if api_key:
        try:
            candidate = generate_with_gemini(findings, api_key)
            accurate, missing = check_accuracy(candidate, findings)

            if accurate:
                narrative = candidate
                mode = "Gemini API"
                print("Gemini generation and accuracy checks passed.")
            else:
                print(
                    "Gemini output failed the accuracy check. "
                    f"Missing figures: {missing}"
                )
                print("Using verified offline fallback.")

        except Exception as error:
            safe_error = str(error).replace(api_key, "[REDACTED]")
            print("Gemini request failed; using offline fallback.")
            print("Error type:", type(error).__name__)
            print("Error details:", safe_error[:1000])

    else:
        print("GEMINI_API_KEY is not set; using offline fallback.")

    if narrative is None:
        narrative = offline_fallback(findings)

    accurate, missing = check_accuracy(narrative, findings)

    if not accurate:
        raise ValueError(
            f"Final narrative is missing required figures: {missing}"
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write(narrative + "\n")

    print(f"Generation mode: {mode}")
    print("Accuracy check: PASSED")
    print(f"Narrative saved to: {OUTPUT_PATH}")
    print("\n" + narrative)


if __name__ == "__main__":
    main()