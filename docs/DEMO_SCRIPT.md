# WeIntern Demo Script

## Demo 1 — Natural language intent recognition

User: `Could you tell me when your support team is available?`

Expected: the LLM classifies `business_hours` even though the exact training example wording is not used.

## Demo 2 — Multi-turn conversation

User: `Where is my order?`

Bot: asks for order ID.

User: `ORD10001`

Bot: gives the local demo order status.

User: `Can I cancel it?`

Bot: uses the prior order context and explains the cancellation path.

## Demo 3 — Knowledge grounding

User: `What payment methods do you accept?`

Bot: uses the local knowledge base and answers with UPI, credit card, debit card, and net banking.

## Demo 4 — Fallback

User: `Explain quantum entanglement.`

Bot: explains that SmartAssist is scoped to NovaCart customer support and suggests supported categories.

## Demo 5 — Error handling

Temporarily remove the API key or exceed the Groq limit, then demonstrate the friendly error message instead of a raw Python exception.
