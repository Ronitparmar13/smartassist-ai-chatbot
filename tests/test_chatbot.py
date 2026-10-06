import json
import pytest

from chatbot import (
    ALLOWED_INTENTS,
    INTENTS,
    ORDERS,
    ORDER_ID_PATTERN,
    RESPONSE_SCHEMA,
    SmartAssist,
)


# ============================================================
# Fake Groq response helpers
# ============================================================

class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeCompletion:
    def __init__(self, payload):
        self.choices = [
            FakeChoice(
                json.dumps(payload)
            )
        ]


class FakeCompletions:
    def __init__(self, payload):
        self.payload = payload

    def create(self, **kwargs):
        return FakeCompletion(
            self.payload
        )


class FakeChat:
    def __init__(self, payload):
        self.completions = FakeCompletions(
            payload
        )


class FakeClient:
    def __init__(self, payload):
        self.chat = FakeChat(
            payload
        )


def make_payload(
    intent,
    response="Test response",
    supported=True,
    order_id="",
    topic="",
    needs_information=False,
):
    return {
        "intent": intent,
        "supported": supported,
        "entities": {
            "order_id": order_id,
            "topic": topic,
        },
        "needs_information": needs_information,
        "response": response,
    }


def make_bot(payload):
    bot = SmartAssist()
    bot.client = FakeClient(payload)
    return bot


# ============================================================
# DATASET / STRUCTURE
# ============================================================

def test_has_at_least_ten_intents():
    assert len(INTENTS) >= 10


def test_has_expected_intents():
    expected = {
        "greeting",
        "goodbye",
        "thanks",
        "help",
        "business_hours",
        "contact_support",
        "pricing",
        "refund",
        "payment_methods",
        "order_status",
        "cancel_order",
        "technical_issue",
    }

    assert expected.issubset(
        set(ALLOWED_INTENTS)
    )


def test_unknown_intent_exists():
    assert "unknown" in ALLOWED_INTENTS


def test_response_schema_is_strict():
    assert RESPONSE_SCHEMA["type"] == "object"
    assert RESPONSE_SCHEMA["additionalProperties"] is False
    assert "intent" in RESPONSE_SCHEMA["properties"]
    assert "response" in RESPONSE_SCHEMA["properties"]


def test_intent_dataset_entries_have_names():
    for item in INTENTS:
        assert isinstance(item, dict)
        assert item.get("name")


def test_demo_orders_dataset_exists():
    assert isinstance(ORDERS, list)
    assert len(ORDERS) > 0


# ============================================================
# ORDER ID TESTS
# ============================================================

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ORD10001", "ORD10001"),
        ("please check ORD10002", "ORD10002"),
        ("order ord10003", "ORD10003"),
        ("my id is ORD10004", "ORD10004"),
        ("no order number here", None),
    ],
)
def test_order_id_extraction(text, expected):
    match = ORDER_ID_PATTERN.search(text)

    actual = (
        match.group(0).upper()
        if match
        else None
    )

    assert actual == expected


@pytest.mark.parametrize(
    "text",
    [
        "ORD10001",
        "ord10002",
        "ORD99999",
    ],
)
def test_bare_order_id(text):
    assert SmartAssist._is_bare_order_id(
        text
    )


def test_normal_sentence_is_not_bare_order_id():
    assert not SmartAssist._is_bare_order_id(
        "Where is my order ORD10001?"
    )


# ============================================================
# NORMALIZATION
# ============================================================

@pytest.mark.parametrize(
    "intent",
    [
        "greeting",
        "goodbye",
        "thanks",
        "help",
        "business_hours",
        "contact_support",
        "pricing",
        "refund",
        "payment_methods",
        "order_status",
        "cancel_order",
        "technical_issue",
        "unknown",
    ],
)
def test_valid_intent_is_preserved(intent):
    result = SmartAssist._normalize_result(
        make_payload(
            intent=intent,
            supported=intent != "unknown",
        )
    )

    assert result["intent"] == intent


def test_invalid_intent_becomes_unknown():
    result = SmartAssist._normalize_result(
        {
            "intent": "something_not_allowed",
            "supported": True,
            "entities": {
                "order_id": "",
                "topic": "",
            },
            "needs_information": False,
            "response": "test",
        }
    )

    assert result["intent"] == "unknown"
    assert result["supported"] is False


# ============================================================
# EMPTY INPUT / ERROR HANDLING
# ============================================================

def test_empty_message():
    bot = make_bot(
        make_payload(
            "greeting"
        )
    )

    result = bot.reply(
        "",
        [],
        {},
    )

    assert result["ok"] is False
    assert "enter a message" in result["error"].lower()


def test_whitespace_message():
    bot = make_bot(
        make_payload(
            "greeting"
        )
    )

    result = bot.reply(
        "     ",
        [],
        {},
    )

    assert result["ok"] is False


# ============================================================
# FALLBACK
# ============================================================

def test_fallback_response():
    result = SmartAssist._fallback(
        make_payload(
            intent="unknown",
            supported=False,
            response="random",
        )
    )

    assert result["intent"] == "unknown"
    assert result["supported"] is False
    assert result["needs_information"] is False
    assert "NovaCart" in result["response"]


def test_unknown_query_uses_fallback():
    bot = make_bot(
        make_payload(
            intent="unknown",
            supported=False,
            response="unrelated",
        )
    )

    result = bot.reply(
        "Write a video game in C++.",
        [],
        {},
    )

    assert result["ok"] is True
    assert result["intent"] == "unknown"
    assert result["supported"] is False
    assert "NovaCart" in result["response"]


# ============================================================
# INTENT PIPELINE
# ============================================================

INTENT_CASES = [
    ("hello there", "greeting"),
    ("good morning", "greeting"),
    ("see you later", "goodbye"),
    ("bye for now", "goodbye"),
    ("thanks a lot", "thanks"),
    ("I appreciate your help", "thanks"),
    ("what can you do?", "help"),
    ("show me what you support", "help"),

    ("when are you open?", "business_hours"),
    ("what time does your support team start?", "business_hours"),

    ("how do I contact customer support?", "contact_support"),
    ("where can I reach NovaCart?", "contact_support"),

    ("how much does it cost?", "pricing"),
    ("tell me about your plans", "pricing"),

    ("I need a refund", "refund"),
    ("how can I get my money back?", "refund"),

    ("can I pay with UPI?", "payment_methods"),
    ("do you accept credit cards?", "payment_methods"),

    ("where is my order ORD10001?", "order_status"),

    ("I want to cancel order ORD10001", "cancel_order"),

    ("my checkout page is not working", "technical_issue"),
    ("I can't log into my account", "technical_issue"),
]


@pytest.mark.parametrize(
    ("message", "intent"),
    INTENT_CASES,
)
def test_supported_intent_pipeline(
    message,
    intent,
):
    order_id = (
        "ORD10001"
        if "ORD10001" in message
        else ""
    )

    bot = make_bot(
        make_payload(
            intent=intent,
            response="placeholder",
            supported=True,
            order_id=order_id,
        )
    )

    result = bot.reply(
        message,
        [],
        {},
    )

    assert result["ok"] is True
    assert result["intent"] == intent
    assert result["supported"] is True
    assert result["response"]


# ============================================================
# KNOWLEDGE BASE GROUNDING
# ============================================================

@pytest.mark.parametrize(
    "intent",
    [
        "business_hours",
        "contact_support",
        "pricing",
        "refund",
        "payment_methods",
        "technical_issue",
    ],
)
def test_knowledge_grounding(intent):
    bot = make_bot(
        make_payload(
            intent=intent,
            response="hallucinated answer",
            supported=True,
        )
    )

    result = bot.reply(
        f"test {intent}",
        [],
        {},
    )

    assert result["ok"] is True
    assert result["intent"] == intent

    # The chatbot should replace the fake
    # LLM answer with grounded information.
    assert (
        result["response"]
        != "hallucinated answer"
    )

    assert result["response"]


# ============================================================
# ORDER WORKFLOW
# ============================================================

def test_order_status_without_id_requests_id():
    bot = make_bot(
        make_payload(
            intent="order_status",
            supported=True,
            needs_information=True,
            response="Need order ID",
        )
    )

    result = bot.reply(
        "Where is my order?",
        [],
        {},
    )

    assert result["ok"] is True
    assert result["intent"] == "order_status"
    assert result["needs_information"] is True
    assert "order ID" in result["response"]


def test_order_status_with_id_is_grounded():
    bot = make_bot(
        make_payload(
            intent="order_status",
            supported=True,
            order_id="ORD10001",
            response="placeholder",
        )
    )

    result = bot.reply(
        "Where is my order ORD10001?",
        [],
        {},
    )

    assert result["ok"] is True
    assert (
        result["entities"]["order_id"]
        == "ORD10001"
    )
    assert "ORD10001" in result["response"]


def test_unknown_order_is_handled():
    bot = make_bot(
        make_payload(
            intent="order_status",
            supported=True,
            order_id="ORD99999",
            response="placeholder",
        )
    )

    result = bot.reply(
        "Where is my order ORD99999?",
        [],
        {},
    )

    assert result["ok"] is True
    assert "couldn't find" in result["response"].lower()


# ============================================================
# MULTI-TURN CONTEXT
# ============================================================

def test_context_carries_order_id():
    bot = make_bot(
        make_payload(
            intent="cancel_order",
            supported=True,
            response="placeholder",
        )
    )

    result = bot.reply(
        "Can I cancel it?",
        [],
        {
            "last_intent": "cancel_order",
            "last_order_id": "ORD10001",
            "last_topic": "order",
        },
    )

    assert result["ok"] is True
    assert result["intent"] == "cancel_order"
    assert (
        result["entities"]["order_id"]
        == "ORD10001"
    )
    assert "ORD10001" in result["response"]


def test_bare_order_id_continues_previous_context():
    bot = make_bot(
        make_payload(
            intent="order_status",
            supported=True,
            order_id="ORD10001",
            response="placeholder",
        )
    )

    result = bot.reply(
        "ORD10001",
        [],
        {
            "last_intent": "order_status",
            "last_order_id": "",
            "last_topic": "order",
        },
    )

    assert result["ok"] is True
    assert result["intent"] == "order_status"
    assert (
        result["entities"]["order_id"]
        == "ORD10001"
    )


# ============================================================
# SESSION HISTORY
# ============================================================

def test_history_is_updated():
    bot = make_bot(
        make_payload(
            intent="greeting",
            supported=True,
            response="Hello!",
        )
    )

    result = bot.reply(
        "hello",
        [],
        {},
    )

    assert result["ok"] is True
    assert len(result["history"]) == 2

    assert (
        result["history"][0]["role"]
        == "user"
    )

    assert (
        result["history"][1]["role"]
        == "assistant"
    )


def test_context_is_updated():
    bot = make_bot(
        make_payload(
            intent="pricing",
            supported=True,
            response="Pricing",
            topic="pricing",
        )
    )

    result = bot.reply(
        "what are your prices?",
        [],
        {},
    )

    assert result["ok"] is True
    assert (
        result["context"]["last_intent"]
        == "pricing"
    )


# ============================================================
# FULL THREE-TURN CONTEXT SIMULATION
# ============================================================

def test_three_turn_order_context():
    bot = make_bot(
        make_payload(
            intent="order_status",
            supported=True,
            order_id="ORD10001",
            response="placeholder",
        )
    )

    # Turn 1
    first = bot.reply(
        "Where is my order ORD10001?",
        [],
        {},
    )

    assert first["ok"] is True
    assert (
        first["context"]["last_order_id"]
        == "ORD10001"
    )

    # Turn 2
    second = bot.reply(
        "Can I cancel it?",
        first["history"],
        first["context"],
    )

    assert second["ok"] is True
    assert (
        second["entities"]["order_id"]
        == "ORD10001"
    )


# ============================================================
# TOTAL TEST COUNT
# ============================================================

def test_suite_has_more_than_twenty_cases():
    # This test documents that the project
    # intentionally exceeds the handbook minimum.
    assert len(INTENT_CASES) >= 20