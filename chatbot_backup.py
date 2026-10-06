import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from groq import Groq
except ImportError:  # Allows data/schema tests before dependencies are installed.
    Groq = None

from config import Config

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

INTENTS = json.loads((DATA_DIR / "intents.json").read_text(encoding="utf-8"))
KNOWLEDGE_BASE = json.loads((DATA_DIR / "knowledge_base.json").read_text(encoding="utf-8"))
ORDERS = json.loads((DATA_DIR / "orders.json").read_text(encoding="utf-8"))

ALLOWED_INTENTS = [item["name"] for item in INTENTS] + ["unknown"]

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ALLOWED_INTENTS},
        "supported": {"type": "boolean"},
        "entities": {
            "type": "object",
            "properties": {
                "order_id": {"type": ["string", "null"]},
                "topic": {"type": ["string", "null"]}
            },
            "required": ["order_id", "topic"],
            "additionalProperties": False
        },
        "needs_information": {"type": "boolean"},
        "response": {"type": "string"}
    },
    "required": ["intent", "supported", "entities", "needs_information", "response"],
    "additionalProperties": False
}

SYSTEM_PROMPT = """
You are SmartAssist, a professional customer-support chatbot for the fictional company NovaCart.

Your job is to understand the user's message, identify exactly one supported intent, use conversation context,
and produce a concise, friendly response grounded ONLY in the supplied knowledge base and order data.

Supported intents:
- greeting: user greets the assistant.
- goodbye: user ends the conversation.
- thanks: user expresses gratitude.
- help: user asks what the assistant can help with.
- business_hours: user asks about support/business hours.
- contact_support: user asks how to contact support.
- pricing: user asks about plans or prices.
- refund: user asks about refund policy or requesting a refund.
- payment_methods: user asks about supported payment methods.
- order_status: user asks to track/check an order.
- cancel_order: user asks to cancel an order.
- technical_issue: user reports login, website, app, or technical problems.

If the user's request is unrelated to these capabilities, use intent=unknown, supported=false,
and give a helpful fallback explaining the supported areas.

Never invent policies, prices, contact details, order statuses, or capabilities.
Never claim that an action was actually completed when the app only explains a process.
For order questions, use only the supplied order records. If an order ID is missing, ask for it.
For an order ID that does not exist in the records, say that the demo system could not find it.

Return ONLY the structured response matching the supplied schema.
""".strip()


class SmartAssist:
    def __init__(self):
        self.client = None
        if Groq is not None and Config.GROQ_API_KEY:
            self.client = Groq(api_key=Config.GROQ_API_KEY)

    def reply(self, message: str, history: list, context: dict) -> dict:
        if self.client is None:
            if Groq is None:
                return {"ok": False, "error": "Groq dependency is not installed. Run: pip install -r requirements.txt"}
            return {"ok": False, "error": "GROQ_API_KEY is missing. Add your Groq API key to .env and restart the app."}

        if len(message) > Config.MAX_MESSAGE_CHARS:
            return {
                "ok": False,
                "error": f"Message is too long. Please keep it under {Config.MAX_MESSAGE_CHARS} characters."
            }

        clean_history = self._trim_history(history)
        context = context if isinstance(context, dict) else {}

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({
            "role": "system",
            "content": self._build_context_prompt(context)
        })
        messages.append({
            "role": "system",
            "content": self._build_knowledge_prompt()
        })
        messages.extend(clean_history)
        messages.append({"role": "user", "content": message})

        try:
            completion = self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=messages,
                temperature=0.2,
                max_tokens=300,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "smartassist_response",
                        "strict": True,
                        "schema": SCHEMA
                    }
                }
            )
        except Exception as exc:
            return {
                "ok": False,
                "error": self._friendly_api_error(exc)
            }

        raw = completion.choices[0].message.content
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "ok": False,
                "error": "The AI returned an unexpected response format. Please try again."
            }

        result = self._validate_and_ground(result, message)

        new_history = clean_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result["response"]}
        ]

        new_context = {
            "last_intent": result["intent"],
            "last_order_id": result["entities"].get("order_id"),
            "last_topic": result["entities"].get("topic"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        self._append_log(message, result, new_context)

        return {
            "ok": True,
            "response": result["response"],
            "intent": result["intent"],
            "supported": result["supported"],
            "needs_information": result["needs_information"],
            "history": new_history,
            "context": new_context
        }

    def _build_context_prompt(self, context: dict) -> str:
        return (
            "Conversation context from the application:\n"
            f"{json.dumps(context, ensure_ascii=False)}\n"
            "Use it only to resolve follow-up messages; do not invent missing information."
        )

    def _build_knowledge_prompt(self) -> str:
        return (
            "Authoritative demo knowledge base:\n"
            f"{json.dumps(KNOWLEDGE_BASE, ensure_ascii=False, indent=2)}\n\n"
            "Authoritative demo orders:\n"
            f"{json.dumps(ORDERS, ensure_ascii=False, indent=2)}"
        )

    @staticmethod
    def _trim_history(history: list) -> list:
        valid = []
        for item in history:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                valid.append({"role": role, "content": content})
        return valid[-Config.MAX_HISTORY_MESSAGES:]

    def _validate_and_ground(self, result: dict, message: str) -> dict:
        if result.get("intent") not in ALLOWED_INTENTS:
            result["intent"] = "unknown"
            result["supported"] = False

        if result["intent"] == "unknown" or not result["supported"]:
            result["intent"] = "unknown"
            result["supported"] = False
            result["needs_information"] = False
            result["response"] = (
                "I'm currently designed to help with pricing, orders, refunds, payments, "
                "support, business hours, and technical issues. Could you ask me something related to those areas?"
            )
            return result

        order_id = result["entities"].get("order_id")
        if order_id:
            order_id = order_id.strip().upper()
            if re.fullmatch(r"[A-Z]{3}\d{5}", order_id):
                result["entities"]["order_id"] = order_id
            else:
                result["entities"]["order_id"] = None

        if result["intent"] in {"order_status", "cancel_order"}:
            resolved_id = result["entities"].get("order_id")
            if resolved_id:
                order = next((x for x in ORDERS if x["order_id"] == resolved_id), None)
                if not order:
                    result["needs_information"] = False
                    result["response"] = (
                        f"I couldn't find demo order {resolved_id}. Please double-check the order ID and try again."
                    )
                elif result["intent"] == "order_status":
                    result["needs_information"] = False
                    result["response"] = (
                        f"Order {order['order_id']} is currently {order['status'].lower()}. "
                        f"Expected delivery: {order['estimated_delivery']}."
                    )
                elif result["intent"] == "cancel_order":
                    if order["status"] in {"Shipped", "Out for Delivery", "Delivered"}:
                        result["needs_information"] = False
                        result["response"] = (
                            f"Order {order['order_id']} is already {order['status'].lower()}, so cancellation is not available in the demo. "
                            "You can contact support for the next available option."
                        )
                    else:
                        result["needs_information"] = False
                        result["response"] = (
                            f"Order {order['order_id']} is eligible for cancellation in the demo workflow. "
                            "Please contact support to complete the request."
                        )
            else:
                result["needs_information"] = True
                result["response"] = "Sure. Please provide your order ID so I can help you with that."

        if result["intent"] == "technical_issue" and not result["response"]:
            result["response"] = KNOWLEDGE_BASE["technical_support"]["message"]

        if result["intent"] == "pricing":
            result["response"] = (
                f"Our plans are {KNOWLEDGE_BASE['pricing']['plans']}. "
                f"{KNOWLEDGE_BASE['pricing']['note']}"
            )

        if result["intent"] == "business_hours":
            result["response"] = KNOWLEDGE_BASE["business_hours"]

        if result["intent"] == "contact_support":
            result["response"] = KNOWLEDGE_BASE["support_contact"]

        if result["intent"] == "payment_methods":
            result["response"] = KNOWLEDGE_BASE["payment_methods"]

        if result["intent"] == "refund":
            result["response"] = KNOWLEDGE_BASE["refund_policy"]

        return result

    @staticmethod
    def _friendly_api_error(exc: Exception) -> str:
        text = str(exc).lower()
        if "401" in text or "authentication" in text or "api key" in text:
            return "Groq authentication failed. Please check GROQ_API_KEY in your .env file."
        if "429" in text or "rate limit" in text:
            return "The Groq free-plan limit was reached. Please wait a little and try again."
        return "I couldn't reach the AI service right now. Please try again in a moment."

    @staticmethod
    def _append_log(message: str, result: dict, context: dict) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = LOG_DIR / "conversations.json"
        records = []
        if path.exists():
            try:
                records = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                records = []

        records.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": message,
            "intent": result["intent"],
            "supported": result["supported"],
            "response": result["response"],
            "context": context
        })

        path.write_text(json.dumps(records[-1000:], indent=2, ensure_ascii=False), encoding="utf-8")
