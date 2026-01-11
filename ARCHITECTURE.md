# AI Digital Twin - Technical Architecture

## System Overview

```
+-----------------------------------------------------------------------------+
|                              USER BROWSER                                    |
|  +-----------------------------------------------------------------------+  |
|  |                     React Frontend (Netlify)                          |  |
|  |  +-----------------+    +----------------------------------------+   |  |
|  |  |   ChatWindow    |    |         App Header                     |   |  |
|  |  |   - Messages    |    |   - Title + New Chat button            |   |  |
|  |  |   - Input       |    |                                        |   |  |
|  |  |   - Feedback    |    +----------------------------------------+   |  |
|  |  +-----------------+                                                  |  |
|  +-----------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------+
                                      |
                                      | HTTPS (REST API)
                                      v
+-----------------------------------------------------------------------------+
|                      FastAPI Backend (Render)                                |
|  +-----------------------------------------------------------------------+  |
|  |                         API Layer                                      |  |
|  |   POST /api/chat      - Handle chat messages                          |  |
|  |   POST /api/feedback  - Log user feedback (thumbs up/down)            |  |
|  |   POST /api/analytics - Track events (visits, messages)               |  |
|  |   GET  /api/health    - Health check + kill switch status             |  |
|  +-----------------------------------------------------------------------+  |
|                                      |                                       |
|  +-----------------------------------------------------------------------+  |
|  |                       AI Pipeline (ADTPipeline)                        |  |
|  |   +------------+   +-------------+   +------------+   +------------+  |  |
|  |   | 0. Identity| > | 1. Input    | > | 2. RAG     | > | 3. LLM     |  |  |
|  |   | Detection  |   | Guardrails  |   | Retrieval  |   | (Groq API) |  |  |
|  |   +------------+   +-------------+   +------------+   +------------+  |  |
|  |                                                              |         |  |
|  |                                           +------------------+         |  |
|  |                                           v                            |  |
|  |                                    +-------------+                     |  |
|  |                                    | 4. Output   |                     |  |
|  |                                    | Guardrails  |                     |  |
|  |                                    +-------------+                     |  |
|  +-----------------------------------------------------------------------+  |
|                                      |                                       |
|  +---------------------+   +--------------------------------------------+   |
|  |   Training Data     |   |            SQLite Database                 |   |
|  |   (Text Files)      |   |   - conversations (session tracking)       |   |
|  |   - hobbies.txt     |   |   - messages (chat history)                |   |
|  |   - personality.txt |   |   - feedback (user ratings + auto-logged)  |   |
|  |   - interview_      |   |   - analytics (privacy-friendly events)    |   |
|  |     responses.txt   |   |                                            |   |
|  |   - family_and_     |   +--------------------------------------------+   |
|  |     friends.txt     |                                                    |
|  |   - opinions.txt    |                                                    |
|  |   - about_this_     |                                                    |
|  |     project.txt     |                                                    |
|  +---------------------+                                                    |
+-----------------------------------------------------------------------------+
                                      |
                                      | API Call
                                      v
+-----------------------------------------------------------------------------+
|                        Groq Cloud (Free Tier)                                |
|                    Open-source LLM (llama-3.1-8b-instant)                   |
+-----------------------------------------------------------------------------+
```

## Component Details

### 1. Frontend (React + Vite)

**Location**: `frontend/`

**Tech Stack**:
- React 18
- Vite (build tool)
- Framer Motion (animations)

**Key Components**:
- `App.jsx` - Root component with header and chat layout
- `ChatWindow.jsx` - Main chat interface with message history and input
- `MessageBubble.jsx` - Individual message display with typing animation
- `FeedbackModal.jsx` - Thumbs up/down feedback with optional notes

**Custom Hooks**:
- `useChat.js` - Manages chat state, API calls, session ID, feedback submission

**State Management**: React hooks (useState) - no external library needed for this scope.

**API Communication**: Fetch API with async/await.

**Structure**:
```
frontend/
├── src/
│   ├── main.jsx           # Entry point
│   ├── App.jsx             # Root component
│   ├── components/
│   │   ├── index.js        # Component exports
│   │   ├── ChatWindow.jsx  # Chat interface
│   │   ├── MessageBubble.jsx # Message display
│   │   └── FeedbackModal.jsx # Feedback UI
│   ├── hooks/
│   │   └── useChat.js      # Chat state management
│   └── styles/
│       └── index.css       # Global styles
├── package.json
└── vite.config.js
```

### 2. Backend (FastAPI)

**Location**: `backend/`

**Tech Stack**:
- FastAPI (web framework)
- SQLAlchemy (ORM)
- SQLite (database)
- Groq SDK (LLM API)
- scikit-learn (TF-IDF for RAG)

**Structure**:
```
backend/
├── main.py              # FastAPI app entry point + rate limiter
├── api/
│   ├── __init__.py      # Router export
│   ├── routes.py        # API endpoint definitions
│   └── models.py        # Pydantic request/response models
├── core/
│   ├── __init__.py      # Pipeline export
│   ├── pipeline.py      # ADTPipeline - orchestrates all layers
│   ├── rag.py           # RAG retrieval with TF-IDF
│   ├── llm.py           # Groq API integration + prompt building
│   ├── guardrails.py    # Input/output filtering
│   └── identity.py      # Friend/family detection
├── config/              # OWNER CUSTOMIZES (do not modify)
│   ├── system_prompt.txt   # Personality/identity prompt
│   └── settings.txt        # Model parameters
├── data/                # OWNER CUSTOMIZES (do not modify)
│   └── *.txt            # Training text files
├── db/
│   ├── __init__.py      # Database exports
│   ├── database.py      # SQLite connection + session
│   └── models.py        # SQLAlchemy models
└── requirements.txt
```

### 3. AI Pipeline (ADTPipeline)

The pipeline orchestrates response generation through multiple stages:

#### Stage 0: Identity Detection
**Purpose**: Recognize friends/family for personalized tone.

**Implementation** (`core/identity.py`):
- Parses names from `family_and_friends.txt`
- Scans conversation for self-identification patterns ("I'm Kyle", "This is Bri")
- Returns `IdentityMatch` with relationship type (family/partner/friend)
- Enables relaxed, casual tone for recognized individuals

#### Stage 1: Input Guardrails
**Purpose**: Block inappropriate or manipulative queries.

**Implementation** (`core/guardrails.py`):
- **Blocked Topics**: Politics, religion, sensitive social issues, financial info
- **Jailbreak Detection**: Prompt injection, role override attempts
- **Manipulation Detection**: Social engineering, false claims about Cameron
- **Inappropriate Content**: Profanity, harmful requests

#### Stage 2: RAG Retrieval
**Purpose**: Retrieve relevant personal information based on user query.

**Implementation** (`core/rag.py`):
- Load all `.txt` files from `data/` directory
- Split into chunks (section-based with ## headers, or paragraph-based)
- Use TF-IDF vectorization with unigrams/bigrams
- Query expansion for common interview questions (weakness -> weaknesses, flaw, struggle)
- Return top-K relevant chunks as context (default: 3)

**Why TF-IDF over embeddings?**: Lightweight, fast, no external API costs. Sufficient for small personal datasets.

#### Stage 3: LLM Generation
**Purpose**: Generate response using retrieved context + personality prompt.

**Implementation** (`core/llm.py`):
- Loads system prompt from `config/system_prompt.txt`
- Loads parameters from `config/settings.txt`
- Builds multi-part prompt: personality + style + guardrails + context + identity
- Enforces third-person perspective (speaks ABOUT Cameron, not AS Cameron)
- First message always asks who the user is
- Uses Groq API with `llama-3.1-8b-instant` model

**Groq Free Tier Limits**:
- 30 requests/minute (matched by rate limiter)
- 14,400 requests/day
- Sufficient for personal project

#### Stage 4: Output Guardrails
**Purpose**: Filter inappropriate content before sending to user.

**Implementation** (`core/guardrails.py`):
- Fabrication detection (AI-like phrasing, over-specific dates)
- Negative owner statement detection (won't criticize Cameron)
- Blocked topic re-check (model might slip)
- Uncertainty detection -> auto-logs feedback + offers contact info
- Inappropriate language cleaning

### 4. Database (SQLite + SQLAlchemy)

**Tables** (`db/models.py`):

```sql
-- Conversation sessions for context
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,   -- UUID from frontend
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual messages
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id VARCHAR(36) REFERENCES conversations(id),
    role VARCHAR(10) NOT NULL,    -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback for model improvement
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id VARCHAR(36),
    user_message TEXT NOT NULL,
    assistant_response TEXT,
    feedback_type VARCHAR(20) NOT NULL,  -- 'unanswered', 'helpful', 'unhelpful', etc.
    rating VARCHAR(10),                   -- 'positive' or 'negative'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Privacy-friendly analytics
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(20) NOT NULL,      -- 'visit', 'message', 'feedback'
    session_id VARCHAR(36),
    event_data TEXT,                       -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Flow

1. **User sends message** -> Frontend
2. **Frontend** -> `POST /api/chat` with message + session_id + optional history
3. **Backend** receives request:
   a. Check kill switch (`CHAT_ENABLED` env var)
   b. Get/create conversation in SQLite
   c. **Identity Detection**: Check if user is recognized friend/family
   d. **Input Guardrails**: Block jailbreaks, manipulation, blocked topics
   e. **RAG**: Query training data for relevant context
   f. **LLM**: Build prompt (personality + style + guardrails + context + identity) -> Groq API
   g. **Output Guardrails**: Validate response, detect uncertainty
   h. Store messages in SQLite
   i. Auto-log feedback if uncertainty detected
4. **Backend** -> Response to Frontend (with metadata: blocked, uncertainty, identity)
5. **Frontend** displays message with typing animation
6. **User can submit feedback** -> `POST /api/feedback` with thumbs up/down + notes

## Configuration

### `backend/config/system_prompt.txt`
Controls the AI's identity and behavior:
- Who the AI is (Cameron's digital assistant)
- Communication style and tone
- What topics to discuss or avoid
- Personality traits

### `backend/config/settings.txt`
Controls model parameters:
- `temperature` - Creativity (0.0-1.0, default: 0.7)
- `max_tokens` - Response length (default: 500)
- `history_limit` - Conversation context size (default: 20)
- `rag_top_k` - How many data chunks to retrieve (default: 3)
- `additional_instructions` - Extra rules appended to system prompt

## Deployment

### Frontend (Netlify)
- **Live URL**: https://cameron-digital-twin.netlify.app/
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_URL` (backend URL)

### Backend (Render)
- Connect GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variables:
  - `GROQ_API_KEY` (from https://console.groq.com)
  - `ALLOWED_ORIGINS` (frontend URL for CORS)
  - `CHAT_ENABLED` (kill switch, default: true)
  - `LLM_MODEL` (optional, default: llama-3.1-8b-instant)

## Security Measures

1. **Rate Limiting**: 30 requests/minute per IP (sliding window)
2. **Input Sanitization**: Guardrails check all user inputs
3. **CORS**: Restricted to frontend domain in production
4. **No PII Storage**: Analytics are privacy-friendly (no personal data)
5. **Kill Switch**: `CHAT_ENABLED=false` disables chat
6. **Jailbreak Protection**: Detects and blocks prompt injection attempts
7. **Manipulation Protection**: Detects social engineering attempts
8. **Output Filtering**: Prevents negative/fabricated statements about owner

## Key Design Decisions

1. **Third-Person Perspective**: AI speaks ABOUT Cameron, not AS Cameron. Prevents identity confusion.
2. **TF-IDF over Embeddings**: Lightweight, no API costs, sufficient for small datasets.
3. **Query Expansion**: Maps common interview questions to training data terminology.
4. **Identity Detection**: Enables relaxed tone for recognized friends/family.
5. **Auto-Feedback Logging**: Uncertainty responses are logged for training data improvement.
6. **Framer Motion**: Provides smooth animations for chat messages and UI interactions.
