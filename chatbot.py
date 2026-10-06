import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from groq import Groq
except ImportError:
    Groq = None

from config import Config


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

INTENTS_PATH = DATA_DIR / "intents.json"
KNOWLEDGE_PATH = DATA_DIR / "knowledge_base.json"
ORDERS_PATH = DATA_DIR / "orders.json"


# =========================================================
# DATA LOADING
# =========================================================

def load_json(path: Path, default: Any) -> Any:
    """Load JSON from a file safely."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


INTENTS = load_json(INTENTS_PATH, [])
KNOWLEDGE_BASE = load_json(KNOWLEDGE_PATH, {})
ORDERS = load_json(ORDERS_PATH, [])


# =========================================================
# INTENTS
# =========================================================

DEFAULT_INTENTS = [
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
]

dataset_intents = [
    item.get("name")
    for item in INTENTS
    if isinstance(item, dict)
    and isinstance(item.get("name"), str)
    and item.get("name").strip()
]

# Keep the expected intents available even if the dataset is
# incomplete, while preserving any additional dataset intents.
ALLOWED_INTENTS = []

for intent in DEFAULT_INTENTS + dataset_intents:
    intent = intent.strip()

    if intent and intent not in ALLOWED_INTENTS:
        ALLOWED_INTENTS.append(intent)

if "unknown" not in ALLOWED_INTENTS:
    ALLOWED_INTENTS.append("unknown")


# =========================================================
# REGEX
# =========================================================

ORDER_ID_PATTERN = re.compile(
    r"\bORD\d{5}\b",
    re.IGNORECASE,
)


# =========================================================
# STRUCTURED OUTPUT SCHEMA
# =========================================================

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": ALLOWED_INTENTS,
        },
        "supported": {
            "type": "boolean",
        },
        "entities": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                },
                "topic": {
                    "type": "string",
                },
            },
            "required": [
                "order_id",
                "topic",
            ],
            "additionalProperties": False,
        },
        "needs_information": {
            "type": "boolean",
        },
        "response": {
            "type": "string",
        },
    },
    "required": [
        "intent",
        "supported",
        "entities",
        "needs_information",
        "response",
    ],
    "additionalProperties": False,
}


# Backwards-compatible alias used by tests.
SCHEMA = RESPONSE_SCHEMA


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are SmartAssist, the customer-support AI for the fictional
company NovaCart.

Your job is to understand natural-language customer messages,
identify the user's PRIMARY PURPOSE, extract useful entities,
use conversation context, and return a concise helpful response.

SUPPORTED INTENTS:

- greeting
- goodbye
- thanks
- help
- business_hours
- contact_support
- pricing
- refund
- payment_methods
- order_status
- cancel_order
- technical_issue
- unknown


INTENT CLASSIFICATION GUIDANCE:

greeting:
Use this ONLY when the user is primarily greeting the assistant.

Examples:
- "Hi"
- "Hello"
- "Hello there"
- "Good morning"
- "Hey SmartAssist"
- "Hey"


help:
Use this when the user is asking for assistance, asking what the
chatbot can do, or asking about available capabilities.

Examples:
- "What can you help me with?"
- "What can you do?"
- "Show me what you can do"
- "What features do you support?"
- "What can you assist with?"
- "I need some help"
- "Can you help me?"
- "How can you help me?"

IMPORTANT:
If a message begins with a greeting but then contains a clear
request for assistance, classify it as HELP rather than GREETING.

Example:
"Hi, I need some help" -> help
"Hello, what can you do?" -> help
"Hey, can you help me with an order?" -> order_status/cancel_order
depending on the actual request.


goodbye:
Use when the user is ending the conversation.

Examples:
- "Bye"
- "Goodbye"
- "See you later"
- "That's all, thanks"


thanks:
Use when the user is mainly expressing gratitude.

Examples:
- "Thanks"
- "Thank you"
- "Thanks for your help"
- "Appreciate it"


business_hours:
Use when asking when NovaCart support/business operations are open.


contact_support:
Use when asking how to contact NovaCart support.


pricing:
Use when asking about NovaCart pricing, plans, cost, charges,
or subscription prices.


refund:
Use when asking about refunds, refund eligibility, or refund policy.


payment_methods:
Use when asking which payment methods NovaCart accepts.


order_status:
Use when asking where an order is, whether an order has shipped,
its status, tracking state, or estimated delivery.


cancel_order:
Use when the user wants to cancel an order or asks whether an
order can be cancelled.


technical_issue:
Use for technical problems involving the NovaCart website,
application, checkout, login, loading, errors, or broken features.


unknown:
Use for unrelated questions, unsupported requests, or requests
that do not match the supported NovaCart intents.


RULES:

1. Choose exactly one intent from the allowed list.

2. Select the intent based on the user's PRIMARY PURPOSE,
   not merely the first words of the message.

3. Return supported=true only for supported NovaCart intents.

4. Return intent=unknown and supported=false for unrelated
   or unsupported requests.

5. Use the supplied NovaCart knowledge base for company facts.

6. Never invent:
   - prices
   - policies
   - support contact details
   - order statuses
   - delivery dates
   - payment options
   - capabilities

7. Use conversation context for follow-up questions.

8. If an order-related request requires an order ID and none is
   known, ask the user for the order ID.

9. If the current message is only an order ID and the previous
   intent was order_status or cancel_order, continue that previous
   order workflow.

10. Never claim that an action was completed when this demo only
    explains the process.

11. Keep responses concise, natural, friendly, and professional.

12. Extract an order ID when one is present.

13. Return an empty string for entities that are not present.

14. Return only the JSON object defined by the supplied schema.
""".strip()


# =========================================================
# SMARTASSIST
# =========================================================

class SmartAssist:
    """LLM-powered NovaCart customer-support chatbot."""

    def __init__(self) -> None:
        self.client = None

        if Groq is not None and Config.GROQ_API_KEY:
            self.client = Groq(
                api_key=Config.GROQ_API_KEY
            )

    # =====================================================
    # PUBLIC API
    # =====================================================

    def reply(
        self,
        message: str,
        history: list,
        context: dict,
    ) -> dict:
        """Generate a response for one user message."""

        # -------------------------------------------------
        # INPUT VALIDATION
        # -------------------------------------------------

        if not isinstance(message, str):
            return self._error(
                "Invalid message."
            )

        message = message.strip()

        if not message:
            return self._error(
                "Please enter a message before sending."
            )

        if len(message) > Config.MAX_MESSAGE_CHARS:
            return self._error(
                f"Please keep your message under "
                f"{Config.MAX_MESSAGE_CHARS} characters."
            )

        # -------------------------------------------------
        # API VALIDATION
        # -------------------------------------------------

        if self.client is None:

            if Groq is None:
                return self._error(
                    "The Groq package is not installed. "
                    "Run: pip install -r requirements.txt"
                )

            return self._error(
                "GROQ_API_KEY is missing. "
                "Add it to your .env file and restart the Flask server."
            )

        # -------------------------------------------------
        # CLEAN INPUT
        # -------------------------------------------------

        clean_history = self._trim_history(
            history
        )

        clean_context = self._clean_context(
            context
        )

        # -------------------------------------------------
        # BUILD MESSAGES
        # -------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": self._build_context_prompt(
                    clean_context
                ),
            },
            {
                "role": "system",
                "content": self._build_knowledge_prompt(),
            },
        ]

        messages.extend(clean_history)

        messages.append(
            {
                "role": "user",
                "content": message,
            }
        )

        # -------------------------------------------------
        # GROQ REQUEST
        # -------------------------------------------------

        try:
            completion = self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=messages,
                temperature=0.2,
                max_completion_tokens=350,
                reasoning_effort="low",
                include_reasoning=False,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "smartassist_response",
                        "strict": True,
                        "schema": RESPONSE_SCHEMA,
                    },
                },
            )

        except Exception as exc:
            return self._error(
                self._friendly_api_error(exc)
            )

        # -------------------------------------------------
        # PARSE RESPONSE
        # -------------------------------------------------

        result = self._parse_completion(
            completion
        )

        if result is None:
            return self._error(
                "The AI returned an unexpected response format. "
                "Please try again."
            )

        # -------------------------------------------------
        # NORMALIZE
        # -------------------------------------------------

        result = self._normalize_result(
            result
        )

        # -------------------------------------------------
        # CONTEXT
        # -------------------------------------------------

        result = self._resolve_context(
            result=result,
            message=message,
            context=clean_context,
        )

        # -------------------------------------------------
        # EXTRA INTENT GUARDRAILS
        # -------------------------------------------------
        # These protect obvious cases where the LLM might
        # classify a very clear phrase incorrectly.

        result = self._apply_intent_guardrails(
            result=result,
            message=message,
        )

        # -------------------------------------------------
        # GROUND AGAINST LOCAL DATA
        # -------------------------------------------------

        result = self._ground_response(
            result=result,
            message=message,
            context=clean_context,
        )

        # -------------------------------------------------
        # UPDATE HISTORY
        # -------------------------------------------------

        new_history = clean_history + [
            {
                "role": "user",
                "content": message,
            },
            {
                "role": "assistant",
                "content": result["response"],
            },
        ]

        new_history = new_history[
            -Config.MAX_HISTORY_MESSAGES:
        ]

        # -------------------------------------------------
        # UPDATE CONTEXT
        # -------------------------------------------------

        new_context = {
            "last_intent": result["intent"],
            "last_order_id": result["entities"].get(
                "order_id",
                "",
            ),
            "last_topic": result["entities"].get(
                "topic",
                "",
            ),
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        # -------------------------------------------------
        # LOG
        # -------------------------------------------------

        self._append_log(
            message=message,
            result=result,
            context=new_context,
        )

        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------

        return {
            "ok": True,
            "response": result["response"],
            "intent": result["intent"],
            "supported": result["supported"],
            "needs_information": result[
                "needs_information"
            ],
            "entities": result["entities"],
            "history": new_history,
            "context": new_context,
        }

    # =====================================================
    # COMPLETION PARSING
    # =====================================================

    @staticmethod
    def _parse_completion(
        completion: Any,
    ) -> dict | None:
        """Extract JSON from a Groq completion."""

        try:
            content = (
                completion
                .choices[0]
                .message
                .content
            )

        except (
            AttributeError,
            IndexError,
            TypeError,
        ):
            return None

        if (
            not isinstance(content, str)
            or not content.strip()
        ):
            return None

        try:
            parsed = json.loads(
                content
            )

        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        return parsed

    # =====================================================
    # NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize_result(
        result: dict,
    ) -> dict:
        """Normalize model output into the expected structure."""

        entities = result.get(
            "entities"
        )

        if not isinstance(
            entities,
            dict,
        ):
            entities = {}

        intent = result.get(
            "intent",
            "unknown",
        )

        if intent not in ALLOWED_INTENTS:
            intent = "unknown"

        supported = bool(
            result.get(
                "supported",
                False,
            )
        )

        if intent == "unknown":
            supported = False

        order_id = str(
            entities.get(
                "order_id",
                "",
            )
            or ""
        ).strip().upper()

        topic = str(
            entities.get(
                "topic",
                "",
            )
            or ""
        ).strip()

        response = str(
            result.get(
                "response",
                "",
            )
            or ""
        ).strip()

        needs_information = bool(
            result.get(
                "needs_information",
                False,
            )
        )

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

    # =====================================================
    # INTENT GUARDRAILS
    # =====================================================

    @staticmethod
    def _apply_intent_guardrails(
        result: dict,
        message: str,
    ) -> dict:
        """
        Correct extremely obvious intent mistakes while still
        using the LLM as the primary intent recognizer.
        """

        text = message.lower().strip()

        # -------------------------------------------------
        # HELP
        # -------------------------------------------------

        help_patterns = [
            "what can you do",
            "show me what you can do",
            "what can you help me with",
            "what can you help with",
            "how can you help me",
            "what features do you support",
            "what features do you have",
            "what do you support",
            "what are your capabilities",
            "what can you assist with",
            "can you help me",
            "i need some help",
        ]

        if any(
            phrase in text
            for phrase in help_patterns
        ):
            result["intent"] = "help"
            result["supported"] = True
            result["needs_information"] = False

            if not result["response"]:
                result["response"] = (
                    "I can help with NovaCart orders, pricing, "
                    "refunds, payments, support, business hours, "
                    "and technical issues."
                )

        # -------------------------------------------------
        # GREETING + HELP
        # -------------------------------------------------

        greeting_starters = (
            "hi ",
            "hi,",
            "hello ",
            "hello,",
            "hey ",
            "hey,",
            "good morning ",
            "good afternoon ",
            "good evening ",
        )

        contains_help_request = any(
            phrase in text
            for phrase in help_patterns
        )

        if (
            text.startswith(greeting_starters)
            and contains_help_request
        ):
            result["intent"] = "help"
            result["supported"] = True

        return result

    # =====================================================
    # CONTEXT RESOLUTION
    # =====================================================

    def _resolve_context(
        self,
        result: dict,
        message: str,
        context: dict,
    ) -> dict:
        """Resolve order IDs and follow-up intent context."""

        detected_order_id = (
            self._extract_order_id(
                message
            )
        )

        previous_intent = context.get(
            "last_intent",
            "",
        )

        previous_order_id = context.get(
            "last_order_id",
            "",
        )

        # -------------------------------------------------
        # CURRENT ORDER ID
        # -------------------------------------------------

        if detected_order_id:
            result["entities"][
                "order_id"
            ] = detected_order_id

        # -------------------------------------------------
        # BARE ORDER ID
        # -------------------------------------------------

        if (
            self._is_bare_order_id(message)
            and previous_intent
            in {
                "order_status",
                "cancel_order",
            }
        ):
            result["intent"] = (
                previous_intent
            )

            result["supported"] = True

            result["entities"][
                "order_id"
            ] = detected_order_id or ""

            result[
                "needs_information"
            ] = False

        # -------------------------------------------------
        # CARRY PREVIOUS ORDER
        # -------------------------------------------------

        if (
            result["intent"]
            in {
                "order_status",
                "cancel_order",
            }
            and not result["entities"].get(
                "order_id"
            )
            and previous_order_id
        ):
            result["entities"][
                "order_id"
            ] = previous_order_id

        return result

    # =====================================================
    # RESPONSE GROUNDING
    # =====================================================

    def _ground_response(
        self,
        result: dict,
        message: str,
        context: dict,
    ) -> dict:
        """
        Replace factual replies with authoritative local
        NovaCart demo data.
        """

        intent = result[
            "intent"
        ]

        # -------------------------------------------------
        # UNKNOWN
        # -------------------------------------------------

        if (
            intent == "unknown"
            or not result["supported"]
        ):
            return self._fallback(
                result
            )

        # -------------------------------------------------
        # BUSINESS HOURS
        # -------------------------------------------------

        if intent == "business_hours":

            result["response"] = KNOWLEDGE_BASE.get(
                "business_hours",
                "Please contact NovaCart support "
                "for business hours.",
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # CONTACT SUPPORT
        # -------------------------------------------------

        elif intent == "contact_support":

            result["response"] = KNOWLEDGE_BASE.get(
                "support_contact",
                "Please use the NovaCart Help Center "
                "to contact support.",
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # PAYMENT METHODS
        # -------------------------------------------------

        elif intent == "payment_methods":

            result["response"] = KNOWLEDGE_BASE.get(
                "payment_methods",
                "Please check the NovaCart checkout "
                "for available payment methods.",
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # REFUND
        # -------------------------------------------------

        elif intent == "refund":

            result["response"] = KNOWLEDGE_BASE.get(
                "refund_policy",
                "Please contact NovaCart support "
                "for refund information.",
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # PRICING
        # -------------------------------------------------

        elif intent == "pricing":

            pricing = KNOWLEDGE_BASE.get(
                "pricing",
                {},
            )

            if not isinstance(
                pricing,
                dict,
            ):
                pricing = {}

            plans = pricing.get(
                "plans",
                "Pricing information is available "
                "in the NovaCart app.",
            )

            note = pricing.get(
                "note",
                "",
            )

            if note:
                result["response"] = (
                    f"{plans}. {note}"
                ).strip()
            else:
                result["response"] = (
                    str(plans)
                ).strip()

            result["needs_information"] = False

        # -------------------------------------------------
        # TECHNICAL ISSUE
        # -------------------------------------------------

        elif intent == "technical_issue":

            technical = KNOWLEDGE_BASE.get(
                "technical_support",
                {},
            )

            if not isinstance(
                technical,
                dict,
            ):
                technical = {}

            result["response"] = technical.get(
                "message",
                "Please refresh the page and "
                "contact support if the issue continues.",
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # ORDER INTENTS
        # -------------------------------------------------

        elif intent in {
            "order_status",
            "cancel_order",
        }:

            self._handle_order_intent(
                result
            )

        # -------------------------------------------------
        # GREETING
        # -------------------------------------------------

        elif intent == "greeting":

            result["response"] = (
                "Hello! I'm SmartAssist. "
                "How can I help you today?"
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # GOODBYE
        # -------------------------------------------------

        elif intent == "goodbye":

            result["response"] = (
                "Goodbye! Have a great day."
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # THANKS
        # -------------------------------------------------

        elif intent == "thanks":

            result["response"] = (
                "You're welcome!"
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # HELP
        # -------------------------------------------------

        elif intent == "help":

            result["response"] = (
                "I can help with NovaCart orders, "
                "pricing, refunds, payments, support, "
                "business hours, and technical issues."
            )

            result["needs_information"] = False

        # -------------------------------------------------
        # SAFETY NET
        # -------------------------------------------------

        if not result["response"]:

            result["response"] = (
                "I can help with NovaCart orders, "
                "pricing, refunds, payments, support, "
                "business hours, and technical issues."
            )

        return result

    # =====================================================
    # ORDER HANDLER
    # =====================================================

    def _handle_order_intent(
        self,
        result: dict,
    ) -> None:
        """Handle order status and cancellation."""

        order_id = result[
            "entities"
        ].get(
            "order_id",
            "",
        )

        # -------------------------------------------------
        # NO ORDER ID
        # -------------------------------------------------

        if not order_id:

            result["needs_information"] = True

            result["response"] = (
                "Sure. Please provide your NovaCart "
                "order ID, for example ORD10001."
            )

            return

        # -------------------------------------------------
        # INVALID ORDER ID
        # -------------------------------------------------

        if not re.fullmatch(
            r"ORD\d{5}",
            order_id,
            re.IGNORECASE,
        ):

            result["entities"][
                "order_id"
            ] = ""

            result["needs_information"] = True

            result["response"] = (
                "Please provide a valid NovaCart "
                "order ID such as ORD10001."
            )

            return

        order_id = order_id.upper()

        result["entities"][
            "order_id"
        ] = order_id

        # -------------------------------------------------
        # LOOK UP DEMO ORDER
        # -------------------------------------------------

        order = next(
            (
                item
                for item in ORDERS
                if (
                    isinstance(
                        item,
                        dict,
                    )
                    and str(
                        item.get(
                            "order_id",
                            "",
                        )
                    ).upper()
                    == order_id
                )
            ),
            None,
        )

        # -------------------------------------------------
        # ORDER NOT FOUND
        # -------------------------------------------------

        if order is None:

            result["needs_information"] = False

            result["response"] = (
                f"I couldn't find demo order {order_id}. "
                "Please double-check the order ID and try again."
            )

            return

        status = str(
            order.get(
                "status",
                "Unknown",
            )
        ).strip()

        delivery = str(
            order.get(
                "estimated_delivery",
                "Unavailable",
            )
        ).strip()

        # -------------------------------------------------
        # ORDER STATUS
        # -------------------------------------------------

        if result["intent"] == "order_status":

            result["needs_information"] = False

            result["response"] = (
                f"Order {order_id} is currently "
                f"{status.lower()}. "
                f"Expected delivery: {delivery}."
            )

            return

        # -------------------------------------------------
        # CANCELLATION
        # -------------------------------------------------

        if status.lower() in {
            "shipped",
            "out for delivery",
            "delivered",
        }:

            result["needs_information"] = False

            result["response"] = (
                f"Order {order_id} is already "
                f"{status.lower()}, so cancellation "
                "is not available in this demo. "
                "Please contact support for the next "
                "available option."
            )

        else:

            result["needs_information"] = False

            result["response"] = (
                f"Order {order_id} is eligible for "
                "cancellation in this demo. "
                "Please contact support to complete "
                "the request."
            )

    # =====================================================
    # FALLBACK
    # =====================================================

    @staticmethod
    def _fallback(
        result: dict,
    ) -> dict:
        """Return the controlled fallback response."""

        result["intent"] = "unknown"
        result["supported"] = False
        result["needs_information"] = False

        result["entities"] = {
            "order_id": "",
            "topic": "",
        }

        result["response"] = (
            "I'm currently designed to help with "
            "NovaCart pricing, orders, refunds, payments, "
            "support, business hours, and technical issues. "
            "Please ask me something related to one of "
            "those areas."
        )

        return result

    # =====================================================
    # CONTEXT PROMPT
    # =====================================================

    @staticmethod
    def _build_context_prompt(
        context: dict,
    ) -> str:
        """Build a safe context prompt."""

        safe_context = {
            "last_intent": context.get(
                "last_intent",
                "",
            ),
            "last_order_id": context.get(
                "last_order_id",
                "",
            ),
            "last_topic": context.get(
                "last_topic",
                "",
            ),
        }

        return (
            "APPLICATION CONVERSATION CONTEXT:\n"
            + json.dumps(
                safe_context,
                ensure_ascii=False,
            )
            + "\n\n"
            "Use this context only when resolving follow-up "
            "questions. Never invent missing information."
        )

    # =====================================================
    # KNOWLEDGE PROMPT
    # =====================================================

    @staticmethod
    def _build_knowledge_prompt() -> str:
        """Build the authoritative NovaCart knowledge prompt."""

        knowledge_json = json.dumps(
            KNOWLEDGE_BASE,
            ensure_ascii=False,
            indent=2,
        )

        orders_json = json.dumps(
            ORDERS,
            ensure_ascii=False,
            indent=2,
        )

        return (
            "AUTHORITATIVE NOVACART DEMO KNOWLEDGE BASE:\n\n"
            + knowledge_json
            + "\n\n"
            "AUTHORITATIVE NOVACART DEMO ORDERS:\n\n"
            + orders_json
        )

    # =====================================================
    # HISTORY HELPERS
    # =====================================================

    @staticmethod
    def _trim_history(
        history: list,
    ) -> list:
        """Keep only valid recent chat history."""

        if not isinstance(
            history,
            list,
        ):
            return []

        valid = []

        for item in history:

            if not isinstance(
                item,
                dict,
            ):
                continue

            role = item.get(
                "role"
            )

            content = item.get(
                "content"
            )

            if (
                role in {
                    "user",
                    "assistant",
                }
                and isinstance(
                    content,
                    str,
                )
                and content.strip()
            ):
                valid.append(
                    {
                        "role": role,
                        "content": content.strip(),
                    }
                )

        return valid[
            -Config.MAX_HISTORY_MESSAGES:
        ]

    # =====================================================
    # CONTEXT CLEANING
    # =====================================================

    @staticmethod
    def _clean_context(
        context: dict,
    ) -> dict:
        """Clean session context."""

        if not isinstance(
            context,
            dict,
        ):
            return {}

        return {
            "last_intent": str(
                context.get(
                    "last_intent",
                    "",
                )
            )[:80],

            "last_order_id": str(
                context.get(
                    "last_order_id",
                    "",
                )
            )[:40],

            "last_topic": str(
                context.get(
                    "last_topic",
                    "",
                )
            )[:120],
        }

    # =====================================================
    # ORDER HELPERS
    # =====================================================

    @staticmethod
    def _extract_order_id(
        message: str,
    ) -> str | None:
        """Extract a NovaCart order ID."""

        match = ORDER_ID_PATTERN.search(
            message
        )

        if match:
            return match.group(
                0
            ).upper()

        return None

    @staticmethod
    def _is_bare_order_id(
        message: str,
    ) -> bool:
        """Check whether message contains only an order ID."""

        return bool(
            ORDER_ID_PATTERN.fullmatch(
                message.strip()
            )
        )

    # =====================================================
    # ERROR HANDLING
    # =====================================================

    @staticmethod
    def _error(
        message: str,
    ) -> dict:
        """Return a standard API/application error."""

        return {
            "ok": False,
            "error": message,
        }

    @staticmethod
    def _friendly_api_error(
        exc: Exception,
    ) -> str:
        """Convert technical API errors into user-friendly text."""

        text = str(
            exc
        ).lower()

        # -------------------------------------------------
        # AUTHENTICATION
        # -------------------------------------------------

        if (
            "401" in text
            or "authentication" in text
            or "api key" in text
            or "unauthorized" in text
        ):
            return (
                "Groq authentication failed. "
                "Please check GROQ_API_KEY in your .env file."
            )

        # -------------------------------------------------
        # RATE LIMIT
        # -------------------------------------------------

        if (
            "429" in text
            or "rate limit" in text
        ):
            return (
                "The Groq request limit has been reached. "
                "Please wait a little and try again."
            )

        # -------------------------------------------------
        # TIMEOUT
        # -------------------------------------------------

        if (
            "timeout" in text
            or "timed out" in text
        ):
            return (
                "The AI service took too long to respond. "
                "Please try again."
            )

        # -------------------------------------------------
        # STRUCTURED OUTPUT
        # -------------------------------------------------

        if (
            "400" in text
            and "json" in text
        ):
            return (
                "The Groq model rejected the structured "
                "response request. Please check the selected "
                "model configuration."
            )

        # -------------------------------------------------
        # GENERAL
        # -------------------------------------------------

        return (
            "I couldn't reach the AI service right now. "
            "Please try again in a moment."
        )

    # =====================================================
    # LOGGING
    # =====================================================

    @staticmethod
    def _append_log(
        message: str,
        result: dict,
        context: dict,
    ) -> None:
        """Append one conversation event to conversations.json."""

        LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            LOG_DIR
            / "conversations.json"
        )

        records = []

        # -------------------------------------------------
        # READ EXISTING LOG
        # -------------------------------------------------

        if path.exists():

            try:

                parsed = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

                if isinstance(
                    parsed,
                    list,
                ):
                    records = parsed

            except (
                json.JSONDecodeError,
                OSError,
            ):
                records = []

        # -------------------------------------------------
        # APPEND RECORD
        # -------------------------------------------------

        records.append(
            {
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),

                "user_message": message,

                "intent": result[
                    "intent"
                ],

                "supported": result[
                    "supported"
                ],

                "needs_information": result[
                    "needs_information"
                ],

                "entities": result[
                    "entities"
                ],

                "response": result[
                    "response"
                ],

                "context": context,
            }
        )

        # -------------------------------------------------
        # SAVE LAST 1000 RECORDS
        # -------------------------------------------------

        try:

            path.write_text(
                json.dumps(
                    records[-1000:],
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

        except OSError:
            # Never break the chatbot because logging failed.
            pass