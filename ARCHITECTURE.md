# AI Digital Twin - Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     React Frontend (Vercel)                          │   │
│  │  ┌──────────────────┐    ┌──────────────────────────────────────┐   │   │
│  │  │   Chat Window    │    │         Notes Section                 │   │   │
│  │  │   - Messages     │    │   (Static content from owner)         │   │   │
│  │  │   - Input        │    │                                       │   │   │
│  │  └──────────────────┘    └──────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS (REST API)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Render)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API Layer                                    │   │
│  │   POST /chat    - Handle chat messages                              │   │
│  │   POST /feedback - Log user feedback                                │   │
│  │   GET /health   - Health check                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       AI Pipeline                                    │   │
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────────────────┐   │   │
│  │   │  1. RAG     │ → │ 2. LLM      │ → │  3. Guardrails          │   │   │
│  │   │  Retrieval  │   │  (Groq API) │   │  (Filter + Validate)    │   │   │
│  │   └─────────────┘   └─────────────┘   └─────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌──────────────────────┐   ┌──────────────────────────────────────────┐   │
│  │   Training Data      │   │            SQLite Database               │   │
│  │   (Text Files)       │   │   - Conversations (session context)      │   │
│  │   - hobbies.txt      │   │   - Feedback (unanswered questions)      │   │
│  │   - resume.txt       │   │   - Metrics (usage stats)                │   │
│  │   - personality.txt  │   │                                          │   │
│  └──────────────────────┘   └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ API Call
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Groq Cloud (Free Tier)                                │
│                    Open-source LLM (Llama 3 / Mistral)                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React)

**Location**: `frontend/`

**Key Components**:
- `ChatWindow.jsx` - Main chat interface with message history
- `MessageBubble.jsx` - Individual message display
- `NotesSection.jsx` - Static notes area (placeholder for owner content)
- `App.jsx` - Root component with layout

**State Management**: React hooks (useState, useContext) - no external library needed for this scope.

**API Communication**: Fetch API with async/await.

### 2. Backend (FastAPI)

**Location**: `backend/`

**Structure**:
```
backend/
├── main.py              # FastAPI app entry point
├── api/
│   ├── __init__.py
│   ├── routes.py        # API endpoint definitions
│   └── models.py        # Pydantic request/response models
├── core/
│   ├── __init__.py
│   ├── rag.py           # RAG retrieval logic
│   ├── llm.py           # Groq API integration
│   ├── guardrails.py    # Content filtering
│   └── pipeline.py      # Orchestrates RAG → LLM → Guardrails
├── data/
│   └── *.txt            # Training text files (owner adds these)
├── db/
│   ├── __init__.py
│   ├── database.py      # SQLite connection
│   └── models.py        # SQLAlchemy models
└── requirements.txt
```

### 3. AI Pipeline

#### Layer 1: RAG (Retrieval-Augmented Generation)

**Purpose**: Retrieve relevant personal information based on user query.

**Implementation**:
- Load all `.txt` files from `data/` directory
- Split into chunks (paragraph-based)
- Use simple TF-IDF or keyword matching for retrieval (lightweight, no embedding model needed)
- Return top-K relevant chunks as context

**Why not embeddings?**: To keep it lightweight and avoid additional API costs. TF-IDF is sufficient for small personal datasets.

#### Layer 2: LLM (Groq API)

**Purpose**: Generate response using retrieved context + personality prompt.

**Implementation**:
- System prompt defines owner's personality, communication style, boundaries
- User message + retrieved context sent to Groq API
- Uses `llama-3.1-8b-instant` or `mixtral-8x7b-32768` (both free)

**Groq Free Tier Limits**:
- 30 requests/minute
- 14,400 requests/day
- Sufficient for personal project

#### Layer 3: Guardrails

**Purpose**: Filter inappropriate content before sending to user.

**Implementation**:
1. **Keyword Blocklist**: Reject responses containing blocked terms
2. **Topic Detection**: Simple pattern matching for political/controversial topics
3. **Prompt-based**: System prompt instructs model to decline certain topics
4. **Fallback Response**: If blocked, return polite deflection

### 4. Database (SQLite)

**Tables**:

```sql
-- Conversation sessions for context
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual messages
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT REFERENCES conversations(id),
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback for model improvement
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT,
    user_message TEXT,
    assistant_response TEXT,
    feedback_type TEXT,  -- 'unanswered', 'inappropriate', 'inaccurate'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Flow

1. **User sends message** → Frontend
2. **Frontend** → `POST /chat` with message + session_id
3. **Backend** receives request:
   a. Load conversation history from SQLite
   b. **RAG**: Query training data for relevant context
   c. **LLM**: Build prompt (system + context + history + user message) → Groq API
   d. **Guardrails**: Validate response
   e. Store messages in SQLite
4. **Backend** → Response to Frontend
5. **Frontend** displays message

## Deployment

### Frontend (Vercel)
- Connect GitHub repo
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

## Security Considerations

1. **Rate Limiting**: Implement on backend to prevent abuse
2. **Input Sanitization**: Validate all user inputs
3. **CORS**: Restrict to frontend domain in production
4. **No PII Storage**: Don't log sensitive user information
5. **Kill Switch**: Environment variable to disable chat (`CHAT_ENABLED=false`)

## Future Enhancements (Not in Scope)

- WebSocket for real-time streaming responses
- User authentication for personalized experiences
- Admin dashboard for viewing feedback
- Fine-tuning a custom model on owner's data
