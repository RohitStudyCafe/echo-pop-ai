# Echo Pop Cloud AI Voice Assistant

Cloud-hosted AI voice assistant backend for an unmodified **Amazon Echo Pop**, powered by **OpenAI** (`gpt-4o-mini`) and **Google Gemini** (`gemini-2.0-flash`) via the **Alexa Skills Kit (ASK)**.

---

## 🌟 Key Features

- **Echo Pop Native Hardware**: Uses the Echo Pop's built-in microphone and speaker with no firmware modifications, USB cables, or hardware teardown.
- **Dual AI Providers**: First-class support for both **OpenAI** and **Google Gemini** with sub-second async API calls.
- **Voice-Driven Provider Switching**: Say *"Switch to Gemini"* or *"Use ChatGPT"* at any point during your conversation.
- **Automatic Fallback**: Transparently fails over to the alternate provider if the primary provider times out or encounters an error.
- **Voice-Tuned Output & Latency Optimization**: Automatically strips markdown, code blocks, URLs, and emojis so Alexa speaks naturally. Answers are concise (1–3 sentences) to ensure immediate speech synthesis.
- **Dual-Layer Memory**:
  - **Short-term Context**: Carried seamlessly across turns via Alexa session attributes (sliding window of recent turns).
  - **Persistent History**: SQL database support with a manual setup script (`scripts/init_db.sql`). Safe no-op fallback when database persistence is disabled.
- **ASK Security Verification**: Validates Amazon Echo request certificate chains and timestamp freshness, with a local development toggle.

---

## 📁 Project Structure

```
├── app/
│   ├── alexa/
│   │   ├── intent_router.py      # Handles Launch, AskAI, SwitchProvider, ClearMemory, etc.
│   │   ├── models.py             # Pydantic models for Alexa JSON requests & responses
│   │   ├── response_builder.py   # Builders for Alexa outputSpeech (ask, tell, error)
│   │   └── verifier.py           # Cryptographic signature & timestamp freshness validator
│   ├── memory/
│   │   ├── session_context.py    # Short-term sliding-window session memory
│   │   └── storage.py            # Persistent storage interface (safe fallback when disabled)
│   ├── providers/
│   │   ├── base.py               # Abstract AIProvider interface and schemas
│   │   ├── openai_provider.py    # OpenAI async client
│   │   ├── gemini_provider.py    # Google Gemini async client
│   │   └── router.py             # Provider routing, switching, & fallback logic
│   ├── utils/
│   │   ├── latency.py            # Latency instrumentation & structured metrics
│   │   └── text_cleaner.py       # Strips markdown, emojis, code for crisp Alexa TTS
│   ├── config.py                 # Pydantic Settings configuration
│   └── main.py                   # FastAPI application & webhook endpoints
├── skill_package/
│   ├── skill.json                # Alexa Skill Manifest
│   └── interactionModels/
│       └── custom/
│           └── en-US.json        # ASK interaction model (intents, utterances, slots)
├── scripts/
│   ├── init_db.sql               # Database DDL for PostgreSQL and SQLite (run manually)
│   └── test_alexa_payload.py     # CLI tool to simulate Alexa queries locally
├── tests/                        # 25 automated unit and integration tests
├── .env.example                  # Environment configuration template
├── Dockerfile                    # Container build configuration
├── docker-compose.yml            # VPS docker-compose setup
└── requirements.txt              # Python dependencies
```

---

## 🚀 Quick Start (Local Setup)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
DEFAULT_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
VERIFY_ALEXA_SIGNATURE=false   # Keep false for local testing
```

### 3. Run the Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Check health: `http://localhost:8000/health`

### 4. Test with CLI Utility (No Alexa Required)
In a separate terminal, test the endpoints directly:
```bash
# Launch greeting
python scripts/test_alexa_payload.py launch

# Ask an AI question
python scripts/test_alexa_payload.py ask "Why is the sky blue?"

# Switch provider to Gemini
python scripts/test_alexa_payload.py switch "gemini"

# Clear memory
python scripts/test_alexa_payload.py clear
```

### 5. Run Automated Tests
```bash
python -m pytest tests/ -v
```

---

## 🎙️ Connecting Your Echo Pop

### Step 1: Deploy to Cloud VPS or Public Tunnel
1. Deploy this container on your cloud VPS (DigitalOcean, Hetzner, AWS, etc.):
   ```bash
   docker-compose up -d --build
   ```
2. Or use **Cloudflare Tunnel** / **ngrok** for local testing:
   ```bash
   ngrok http 8000
   ```
   Note the HTTPS URL (e.g. `https://xxxx.ngrok-free.app/api/v1/alexa`).

### Step 2: Configure Alexa Skills Kit Console
1. Go to the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask).
2. Click **Create Skill**:
   - Name: `Cloud Assistant`
   - Primary locale: `English (US)`
   - Model: **Custom**
   - Hosting: **Provision your own**
3. In **Interaction Model** -> **JSON Editor**:
   - Paste the contents of [`skill_package/interactionModels/custom/en-US.json`](skill_package/interactionModels/custom/en-US.json).
   - Click **Save Model** then **Build Model**.
4. In **Endpoint**:
   - Select **HTTPS**.
   - Default Region: Enter your HTTPS endpoint: `https://your-domain.com/api/v1/alexa`
   - SSL Certificate: Select *"My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority"* (or select your custom cert option).
   - Click **Save Endpoints**.
5. Enable **Test** tab:
   - Change testing from "Off" to "Development".

---

## 🗣️ Voice Commands on Echo Pop

| Voice Command | Action |
|---|---|
| *"Alexa, open cloud assistant"* | Launches assistant and opens session |
| *"Tell me how airplanes fly"* | Generates answer with active AI model |
| *"Switch to Gemini"* | Changes provider to Google Gemini for current session |
| *"Switch to OpenAI"* | Changes provider to OpenAI for current session |
| *"Status"* | Spoken status of current active model |
| *"Clear memory"* | Clears conversation memory |
| *"Stop"* or *"Exit"* | Ends the conversation session |

---

## 🗄️ Database Setup (Optional Manual Step)

As per system policy, the application does not automatically run database migrations or connect to live external databases.

If you wish to enable persistent conversation logging across days/weeks:
1. Open [`scripts/init_db.sql`](scripts/init_db.sql).
2. Run the SQL script manually in your PostgreSQL or SQLite database.
3. Update `.env`:
   ```ini
   PERSISTENCE_ENABLED=true
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/echo_ai
   ```
Without this, conversation memory continues to work seamlessly within each session using Alexa session attributes.

