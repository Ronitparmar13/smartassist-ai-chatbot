# SmartAssist AI Chatbot

An AI-powered customer-support chatbot built for the **WeIntern Week 2 Artificial Intelligence assignment**. SmartAssist uses the **Groq API** with **`openai/gpt-oss-20b`** to understand natural-language customer messages, classify their primary intent, maintain multi-turn context, and generate grounded support responses for the fictional company **NovaCart**.

## Project Highlights

- Natural-language customer-support conversations
- **12 supported business intents** plus an `unknown` fallback intent
- LLM-based intent recognition and response generation
- Strict **JSON Schema structured output** from the LLM
- Multi-turn conversation context using Flask session state
- Local NovaCart knowledge base and demo order data
- Order-status and cancellation workflows with demo order IDs
- Controlled fallback for unsupported requests
- Session conversation logging to JSON
- Interactive web chat interface built with Flask, HTML, CSS, and JavaScript
- Automated unit tests plus a live Groq intent-evaluation suite

## Supported Intents

| Intent | Purpose |
|---|---|
| `greeting` | Basic greetings |
| `goodbye` | Ending the conversation |
| `thanks` | Expressions of gratitude |
| `help` | Asking what SmartAssist can do |
| `business_hours` | NovaCart business/support hours |
| `contact_support` | How to contact support |
| `pricing` | Plans, costs, and pricing |
| `refund` | Refund policy and eligibility |
| `payment_methods` | Accepted payment methods |
| `order_status` | Order status, shipping, tracking, delivery |
| `cancel_order` | Order cancellation requests |
| `technical_issue` | Website, app, login, checkout, or technical problems |
| `unknown` | Unsupported or unrelated requests |

## Technology Stack

- **Backend:** Python, Flask
- **LLM:** Groq API
- **Model:** `openai/gpt-oss-20b`
- **Frontend:** HTML5, CSS3, JavaScript
- **Data:** Local JSON files
- **Testing:** pytest + live Groq intent test runner
- **Session state:** Flask sessions

## Architecture

```text
┌───────────────────────────┐
│       Web Chat UI         │
│     HTML/CSS/JavaScript   │
└─────────────┬─────────────┘
              │ POST /chat
              ▼
┌───────────────────────────┐
│       Flask Web App       │
│   Session + API routes    │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│      SmartAssist Core     │
│ Context + history manager │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│        Groq LLM           │
│     gpt-oss-20b model     │
│   Structured JSON output  │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│ Validation + Guardrails   │
│ Intent + entity handling  │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│ Knowledge / Order Ground  │
│    Local JSON datasets    │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│ Response + Session Log    │
│   conversations.json      │
└───────────────────────────┘
```

## Project Structure

```text
smartassist-ai-chatbot/
│
├── app.py
├── chatbot.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── data/
│   ├── intents.json
│   ├── knowledge_base.json
│   └── orders.json
│
├── docs/
│   ├── TEST_CASES.md
│   ├── DEMO_SCRIPT.md
│   ├── SUPPORTED_INTENTS.md
│   ├── ARCHITECTURE.md
│   └── screenshots/
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── assets/
│       └── smartassist-hero.svg
│
├── templates/
│   └── index.html
│
├── tests/
│   ├── test_chatbot.py
│   └── live_intent_test.py
│
└── logs/
    └── conversations.json
```

> Generated cache files and local conversation logs should not be committed to GitHub.

## Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd smartassist-ai-chatbot
```

### 2. Create a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
FLASK_SECRET_KEY=change_this_value
FLASK_DEBUG=true
MAX_HISTORY_MESSAGES=12
MAX_MESSAGE_CHARS=2000
```

Never commit the `.env` file or expose the API key publicly.

### 5. Start the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Health check:

```text
http://127.0.0.1:5000/health
```

## API Routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Loads the chatbot interface |
| `POST` | `/chat` | Sends a message to SmartAssist |
| `POST` | `/clear-chat` | Clears current session context |
| `GET` | `/health` | Basic service health information |

## Demo Order Data

The demo order dataset includes these example orders:

| Order ID | Status |
|---|---|
| `ORD10001` | Processing |
| `ORD10002` | Shipped |
| `ORD10003` | Out for Delivery |
| `ORD10004` | Delivered |

Use an order ID during a conversation to demonstrate context-aware follow-ups.

Example:

```text
User: Where is my order?
SmartAssist: Sure. Please provide your NovaCart order ID, for example ORD10001.

User: ORD10001
SmartAssist: Order ORD10001 is currently processing. Expected delivery: <demo date>.

User: Can I cancel it?
SmartAssist: <context-aware cancellation response>
```

## Example User Prompts

```text
Hello
What can you help me with?
What are your business hours?
How can I contact support?
How much does your Pro plan cost?
Do you accept UPI?
I want a refund
Where is my order?
ORD10001
Can I cancel it?
I cannot log in
The checkout page is not working
Thanks for your help
Goodbye
Tell me a joke about quantum physics
```

## Multi-Turn Context

SmartAssist stores a small conversation state in the Flask session, including:

- Last detected intent
- Last known order ID
- Last topic
- Recent user/assistant message history

This allows follow-up messages such as:

```text
User: Where is my order?
Bot: Please provide your order ID.

User: ORD10001
Bot: Order ORD10001 is currently processing...

User: Can I cancel it?
Bot: ...
```

The application does not claim to perform real-world actions; cancellation and support actions remain demo workflows.

## Knowledge Base Grounding

Business facts are stored in local JSON files so that important support information is not invented by the model.

```text
data/intents.json
        ↓
data/knowledge_base.json
        ↓
data/orders.json
        ↓
SmartAssist validation + response grounding
```

The Python layer validates the returned intent, resolves order context, handles order-specific logic, and replaces key business responses with authoritative local data where appropriate.

## Structured LLM Output

The Groq response is constrained to a JSON Schema containing:

```json
{
  "intent": "order_status",
  "supported": true,
  "entities": {
    "order_id": "ORD10001",
    "topic": "order tracking"
  },
  "needs_information": false,
  "response": "..."
}
```

This makes the model output easier for the backend to validate and process reliably.

## Testing

### Automated local tests

Run:

```bash
python -m pytest -q
```

Latest local result:

```text
70 passed in 0.38s
```

### Live Groq intent evaluation

Run from the project root:

```bash
PYTHONPATH=. python tests/live_intent_test.py
```

The live test suite contains **35 independent intent cases plus 3 multi-turn cases (38 total)** and writes a timestamped CSV report under `reports/`.

Latest recorded result:

```text
PASS:      37/38
FAIL:       1/38
ACCURACY:  97.37%
```

The single disagreement was a borderline example where the test expected `greeting` for:

```text
Hi, I need some help
```

SmartAssist classified it as `help`, because the primary purpose of the message is a request for assistance. The result was kept as-is rather than forcing an artificial 100% score.

## Conversation Logging

During normal operation, interaction metadata is appended to:

```text
logs/conversations.json
```

A log record contains information such as:

- timestamp
- user message
- detected intent
- support status
- extracted entities
- response
- conversation context

The local conversation log is excluded from Git tracking.

## Fallback Behavior

For unsupported questions, SmartAssist returns a controlled response explaining the supported NovaCart topics rather than pretending to answer outside its domain.

Example:

```text
User: Can you explain quantum mechanics?
Bot: I'm currently designed to help with NovaCart pricing, orders,
refunds, payments, support, business hours, and technical issues.
```

## Error Handling

The application includes user-friendly handling for common runtime issues, including:

- Missing message input
- Oversized messages
- Missing Groq API key
- Missing Groq package
- Authentication failures
- Rate limits
- Timeouts
- Invalid structured responses

## Design Direction

The interface uses a minimal, premium visual language inspired by modern voice-assistant/product interfaces, with:

- warm off-white surfaces
- black typography and panels
- neon-lime accents
- responsive layouts
- interactive chat states
- custom SVG visual artwork

The microphone control was intentionally omitted; interaction is text-first through the chat composer.

## Assignment Deliverables

The repository is prepared to contain the main submission components:

- Source code
- Intent dataset
- Knowledge-base and demo-order data
- Automated tests
- Live intent-evaluation report
- Supported-intents documentation
- Architecture/workflow documentation
- Screenshots / demo evidence
- README
- Final project report

## Future Improvements

For a production version, the project could be extended with:

- Real order-service integration
- Persistent user accounts
- PostgreSQL or SQLite storage
- Retrieval-Augmented Generation (RAG)
- Streaming responses
- Admin analytics dashboard
- Authentication and role-based support tools
- Cloud deployment and monitoring

## Author

**Ronit Parmar**

WeIntern — Week 2 Artificial Intelligence Internship Project

---

> SmartAssist is a demonstration project built around a fictional NovaCart support environment. Order data, policies, prices, and support details are intentionally demo data.
