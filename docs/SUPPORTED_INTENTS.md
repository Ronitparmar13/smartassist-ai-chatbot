# SmartAssist AI Chatbot — Supported Intents

## 1. Overview

SmartAssist is a customer-support chatbot for the fictional e-commerce company **NovaCart**. The chatbot uses natural-language input processing with the Groq API and the `openai/gpt-oss-20b` model to identify the user's primary intent and generate a relevant response.

The system supports **12 customer-service intents plus 1 fallback intent (`unknown`)**, for a total of **13 intent labels**.

---

## 2. Intent List

| # | Intent | Purpose |
|---|---|---|
| 1 | `greeting` | Handles simple greetings and opening messages. |
| 2 | `goodbye` | Handles conversation-ending messages. |
| 3 | `thanks` | Handles expressions of gratitude. |
| 4 | `help` | Explains what SmartAssist can help with and its supported capabilities. |
| 5 | `business_hours` | Provides NovaCart business/support operating hours. |
| 6 | `contact_support` | Explains how the customer can contact NovaCart support. |
| 7 | `pricing` | Answers questions about NovaCart pricing, plans, and charges. |
| 8 | `refund` | Handles refund-policy and refund-eligibility questions. |
| 9 | `payment_methods` | Provides supported payment-method information. |
| 10 | `order_status` | Checks the status of a demo order and estimated delivery. |
| 11 | `cancel_order` | Handles order-cancellation requests. |
| 12 | `technical_issue` | Handles website, application, checkout, login, loading, and similar technical problems. |
| 13 | `unknown` | Fallback for unsupported, unrelated, or unrecognized requests. |

---

## 3. Detailed Intent Documentation

### 3.1 `greeting`

**Purpose:**
Recognizes when the user is primarily greeting the chatbot.

**Example inputs:**
- "Hi"
- "Hello"
- "Hello there"
- "Good morning"
- "Hey SmartAssist"

**Expected behavior:**
Return a friendly greeting and invite the user to ask a NovaCart-related question.

**Important classification rule:**
A greeting followed by a clear support request is classified according to the actual request rather than the greeting alone.

Example:
> "Hello, what can you do?" → `help`

---

### 3.2 `goodbye`

**Purpose:**
Recognizes when the user is ending the conversation.

**Example inputs:**
- "Bye"
- "Goodbye"
- "See you later"
- "That's all, thanks"

**Expected behavior:**
Provide a short, polite closing response.

---

### 3.3 `thanks`

**Purpose:**
Recognizes messages whose primary purpose is expressing gratitude.

**Example inputs:**
- "Thanks"
- "Thank you"
- "Thanks for your help"
- "Appreciate it"

**Expected behavior:**
Respond naturally and politely, for example with a brief acknowledgement.

---

### 3.4 `help`

**Purpose:**
Handles requests asking what SmartAssist can do or asking for general assistance.

**Example inputs:**
- "What can you help me with?"
- "What can you do?"
- "Show me what you can do"
- "What features do you support?"
- "I need some help"
- "Can you help me?"
- "How can you help me?"

**Expected behavior:**
Explain the main NovaCart support areas handled by SmartAssist, including orders, pricing, refunds, payments, support, business hours, and technical issues.

**Classification rule:**
If a message starts with a greeting but contains a clear help request, the primary purpose should determine the result.

Example:
> "Hi, I need some help" → `help`

---

### 3.5 `business_hours`

**Purpose:**
Handles questions about NovaCart business or support operating hours.

**Example inputs:**
- "What are your business hours?"
- "When is NovaCart support open?"
- "Are you available on weekends?"

**Expected behavior:**
Return the operating-hours information from the local NovaCart knowledge base.

---

### 3.6 `contact_support`

**Purpose:**
Handles requests asking how to reach NovaCart customer support.

**Example inputs:**
- "How do I contact support?"
- "I want to talk to NovaCart support"
- "Where can I contact customer service?"

**Expected behavior:**
Provide the support-contact information stored in the local knowledge base.

---

### 3.7 `pricing`

**Purpose:**
Handles NovaCart pricing, plan, subscription, and charge-related questions.

**Example inputs:**
- "How much does NovaCart cost?"
- "What are your plans?"
- "Tell me about pricing"
- "How much is the subscription?"

**Expected behavior:**
Return pricing information from the authoritative local knowledge base and avoid inventing prices or plans.

---

### 3.8 `refund`

**Purpose:**
Handles questions about refunds, refund policy, and refund eligibility.

**Example inputs:**
- "Can I get a refund?"
- "What is your refund policy?"
- "How do refunds work?"
- "Am I eligible for a refund?"

**Expected behavior:**
Return the refund-policy information stored in the NovaCart knowledge base.

---

### 3.9 `payment_methods`

**Purpose:**
Handles questions about payment options accepted by NovaCart.

**Example inputs:**
- "What payment methods do you accept?"
- "Can I pay by card?"
- "Do you accept UPI?"
- "How can I pay for my order?"

**Expected behavior:**
Return supported payment methods using the authoritative local knowledge base.

---

### 3.10 `order_status`

**Purpose:**
Handles questions about an order's current status, shipment state, tracking state, or estimated delivery.

**Example inputs:**
- "Where is my order?"
- "Can you check my order status?"
- "Has my order shipped?"
- "When will my order arrive?"
- "Check ORD10001"

**Expected behavior:**
1. Extract the order ID when present.
2. Use the order ID to look up the corresponding demo order.
3. Return the current status and estimated delivery.
4. Ask for an order ID when the request requires one and none is available.

**Multi-turn example:**
> User: "Where is my order?"
>
> SmartAssist: "Please provide your NovaCart order ID..."
>
> User: "ORD10001"
>
> SmartAssist continues the `order_status` workflow using that order ID.

---

### 3.11 `cancel_order`

**Purpose:**
Handles requests to cancel a NovaCart order.

**Example inputs:**
- "I want to cancel my order"
- "Can I cancel ORD10002?"
- "Please cancel my order"
- "Is my order eligible for cancellation?"

**Expected behavior:**
1. Identify the order ID when available.
2. Look up the demo order.
3. Determine whether cancellation is available in the demo workflow.
4. Explain the next step rather than falsely claiming that an order was actually cancelled.

**Safety/accuracy behavior:**
SmartAssist does not claim to have completed a cancellation because the demo does not perform a real transaction.

---

### 3.12 `technical_issue`

**Purpose:**
Handles technical problems with the NovaCart website or application.

**Example inputs:**
- "The website is not loading"
- "Checkout is broken"
- "I can't log in"
- "The app shows an error"
- "The page keeps loading"

**Expected behavior:**
Return the troubleshooting guidance from the local technical-support knowledge base and recommend contacting support when appropriate.

---

### 3.13 `unknown`

**Purpose:**
Acts as the fallback intent for unsupported or unrelated requests.

**Example inputs:**
- "Who won the football match?"
- "Write me a poem"
- "What is the capital of France?"
- "Tell me a random joke"

**Expected behavior:**
The chatbot should not invent an answer outside its defined NovaCart support scope. It should explain the areas it can support and guide the user back to supported topics.

**Fallback principle:**
`unknown` is treated as `supported = false`.

---

## 4. Entity Extraction

SmartAssist extracts useful entities alongside intent classification.

### Supported entities

| Entity | Description | Example |
|---|---|---|
| `order_id` | NovaCart demo order identifier | `ORD10001` |
| `topic` | Optional topic associated with the request | `payment`, `refund`, `technical issue` |

Order IDs follow the demo pattern:

```text
ORD + 5 digits
```

Example:

```text
ORD10001
```

When an order ID is not present, the chatbot can use the previous conversation context where appropriate.

---

## 5. Multi-Turn Context Handling

SmartAssist stores limited session context including:

- Last detected intent
- Last known order ID
- Last detected topic
- Recent conversation history

This allows follow-up messages to be interpreted using the previous turn.

### Example

```text
User: Where is my order?
Assistant: Please provide your NovaCart order ID, for example ORD10001.

User: ORD10001
Assistant: Order ORD10001 is currently ...

User: Can I cancel it?
Assistant: ...
```

The chatbot uses the remembered order ID when it is appropriate and does not invent missing information.

---

## 6. Fallback and Grounding Rules

The chatbot follows these rules when generating responses:

1. Choose exactly one intent from the defined intent set.
2. Use the user's **primary purpose** for classification.
3. Use the local NovaCart knowledge base for company facts.
4. Use the demo orders dataset for order-specific information.
5. Do not invent prices, policies, support contacts, order statuses, delivery dates, or payment methods.
6. Ask for missing order information when required.
7. Never claim a real transaction was completed when the project only demonstrates the workflow.
8. Return `unknown` for unsupported or unrelated requests.

---

## 7. Structured Response Format

The LLM returns a structured JSON object containing:

```json
{
  "intent": "order_status",
  "supported": true,
  "entities": {
    "order_id": "ORD10001",
    "topic": ""
  },
  "needs_information": false,
  "response": "Order ORD10001 is currently shipped. Expected delivery: ..."
}
```

This structured-output design makes the result predictable for the Flask application and allows the frontend to display the generated response together with intent and context information when needed.

---

## 8. Evaluation Note

The project was tested with both local automated tests and live Groq intent tests.

- **Local automated tests:** 70/70 passed.
- **Live Groq intent test:** 37/38 correctly classified.
- **Live intent accuracy:** **97.37%**.

The single live-test mismatch involved the message **"Hi, I need some help"**, where the expected test label was `greeting` but the model selected `help`. The implementation intentionally treats the clear help request as the message's primary purpose.

This is a borderline classification example rather than a failure of the overall support workflow.
