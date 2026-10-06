import csv
import sys
from datetime import datetime
from pathlib import Path

from chatbot import SmartAssist


# ============================================================
# REAL GROQ INTENT TEST CASES
# ============================================================

CASES = [
    # Greeting
    ("Hey there", "greeting"),
    ("Good morning SmartAssist", "greeting"),
    ("Hi, I need some help", "greeting"),

    # Goodbye
    ("That's all, bye", "goodbye"),
    ("Talk to you later", "goodbye"),

    # Thanks
    ("Thanks a lot", "thanks"),
    ("I really appreciate your help", "thanks"),

    # Help
    ("What can you help me with?", "help"),
    ("Show me what you can do", "help"),

    # Business hours
    ("When is your support team available?", "business_hours"),
    ("Are you open on Saturday?", "business_hours"),
    ("What time do you start work?", "business_hours"),

    # Contact support
    ("How can I get in touch with customer support?", "contact_support"),
    ("Where can I contact NovaCart?", "contact_support"),

    # Pricing
    ("How much does your service cost?", "pricing"),
    ("Tell me about your pricing plans", "pricing"),
    ("What will I have to pay?", "pricing"),

    # Refund
    ("I want my money back", "refund"),
    ("Can I get a refund for my purchase?", "refund"),
    ("What is your refund policy?", "refund"),

    # Payment methods
    ("Can I pay using UPI?", "payment_methods"),
    ("Do you accept debit cards?", "payment_methods"),
    ("What payment options do you offer?", "payment_methods"),

    # Order status
    ("Where is my package ORD10001?", "order_status"),
    ("Can you check ORD10002 for me?", "order_status"),
    ("What's happening with my order ORD10003?", "order_status"),

    # Cancel order
    ("I want to cancel order ORD10001", "cancel_order"),
    ("Can I stop my order ORD10002?", "cancel_order"),

    # Technical issue
    ("I can't log into my account", "technical_issue"),
    ("The checkout page is not working", "technical_issue"),
    ("Something is broken on the website", "technical_issue"),

    # Fallback / unknown
    ("Write a Python game for me", "unknown"),
    ("Explain quantum mechanics", "unknown"),
    ("Who won the cricket match yesterday?", "unknown"),
    ("Tell me a joke about physics", "unknown"),
]


def run_independent_tests(bot):
    rows = []

    for index, (message, expected) in enumerate(CASES, start=1):
        print(f"[{index:02d}/{len(CASES)}] {message}")

        result = bot.reply(
            message,
            [],
            {},
        )

        if not result.get("ok"):
            rows.append(
                {
                    "message": message,
                    "expected": expected,
                    "predicted": "ERROR",
                    "supported": False,
                    "pass": False,
                    "response": result.get("error", ""),
                }
            )
            print(f"    ERROR: {result.get('error', '')}")
            continue

        predicted = result.get(
            "intent",
            "unknown",
        )

        passed = predicted == expected

        rows.append(
            {
                "message": message,
                "expected": expected,
                "predicted": predicted,
                "supported": result.get(
                    "supported",
                    False,
                ),
                "pass": passed,
                "response": result.get(
                    "response",
                    "",
                ),
            }
        )

        status = "PASS" if passed else "FAIL"

        print(
            f"    {status} | expected={expected} | predicted={predicted}"
        )


    return rows


def run_multiturn_test(bot):
    """
    Verify that the chatbot carries an order ID
    across turns.
    """

    history = []
    context = {}

    turns = [
        (
            "Where is my order?",
            "order_status",
        ),
        (
            "ORD10001",
            "order_status",
        ),
        (
            "Can I cancel it?",
            "cancel_order",
        ),
    ]

    rows = []

    print()
    print("MULTI-TURN CONTEXT TEST")
    print("-" * 72)

    for index, (message, expected) in enumerate(turns, start=1):

        print(
            f"Turn {index}: {message}"
        )

        result = bot.reply(
            message,
            history,
            context,
        )

        if not result.get("ok"):

            rows.append(
                {
                    "message": message,
                    "expected": expected,
                    "predicted": "ERROR",
                    "supported": False,
                    "pass": False,
                    "response": result.get(
                        "error",
                        "",
                    ),
                }
            )

            print(
                f"    ERROR: {result.get('error', '')}"
            )

            continue


        predicted = result.get(
            "intent",
            "unknown",
        )

        response = result.get(
            "response",
            "",
        )

        new_context = result.get(
            "context",
            {},
        )

        passed = (
            predicted == expected
        )

        # Final turn must retain ORD10001.
        if message == "Can I cancel it?":

            passed = (
                passed
                and new_context.get(
                    "last_order_id",
                    "",
                ) == "ORD10001"
                and "ORD10001" in response
            )


        rows.append(
            {
                "message": message,
                "expected": expected,
                "predicted": predicted,
                "supported": result.get(
                    "supported",
                    False,
                ),
                "pass": passed,
                "response": response,
            }
        )


        status = "PASS" if passed else "FAIL"

        print(
            f"    {status} | expected={expected} | predicted={predicted}"
        )

        history = result.get(
            "history",
            history,
        )

        context = new_context


    return rows


def save_csv(rows, path):
    fieldnames = [
        "message",
        "expected",
        "predicted",
        "supported",
        "pass",
        "response",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    key: row.get(key, "")
                    for key in fieldnames
                }
            )


def main():
    print()
    print("=" * 72)
    print("SMARTASSIST — LIVE GROQ INTENT TEST")
    print("=" * 72)
    print()

    bot = SmartAssist()

    if bot.client is None:
        print(
            "ERROR: Groq client is not configured."
        )
        print(
            "Make sure GROQ_API_KEY is available "
            "in your .env configuration."
        )
        sys.exit(1)

    independent_rows = run_independent_tests(
        bot
    )

    multiturn_rows = run_multiturn_test(
        bot
    )

    rows = (
        independent_rows
        + multiturn_rows
    )

    total = len(rows)

    passed = sum(
        1
        for row in rows
        if row.get("pass")
    )

    failed = total - passed

    accuracy = (
        passed / total * 100
        if total
        else 0
    )

    print()
    print("=" * 72)
    print(f"PASS:     {passed}/{total}")
    print(f"FAIL:     {failed}/{total}")
    print(f"ACCURACY: {accuracy:.2f}%")
    print("=" * 72)

    print()
    print("FAILED TESTS")
    print("-" * 72)

    failures = [
        row
        for row in rows
        if not row.get("pass")
    ]

    if not failures:
        print(
            "None — all tests passed."
        )
    else:
        for row in failures:
            print(
                f"Expected : {row['expected']}"
            )
            print(
                f"Predicted: {row['predicted']}"
            )
            print(
                f"Input    : {row['message']}"
            )
            print(
                f"Response : {row['response']}"
            )
            print()

    reports_dir = (
        Path(__file__).resolve().parents[1]
        / "reports"
    )

    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report_path = (
        reports_dir
        / f"groq_intent_report_{timestamp}.csv"
    )

    save_csv(
        rows,
        report_path,
    )

    print()
    print(
        f"Detailed CSV report saved to:\n{report_path}"
    )
    print()

    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
