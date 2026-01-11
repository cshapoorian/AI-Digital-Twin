# AI Digital Twin

A conversational web application that serves as an AI representation of its owner. Users can chat with the digital twin to learn about the owner's background, interests, personality, and perspectives.

**Live Demo**: [cameron-digital-twin.netlify.app](https://cameron-digital-twin.netlify.app/)

## Features

- **Conversational AI**: Natural chat interface powered by Groq's free LLM API
- **RAG Retrieval**: Finds relevant information from training data using TF-IDF
- **Smart Guardrails**: Blocks inappropriate topics, jailbreak attempts, and manipulation
- **Identity Detection**: Recognizes friends/family for personalized, casual responses
- **Feedback System**: Thumbs up/down ratings with optional notes
- **Privacy-Friendly Analytics**: Tracks usage without storing personal data
- **Responsive Design**: Works on desktop and mobile
- **Smooth Animations**: Framer Motion for polished UI interactions

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite + Framer Motion |
| Backend | Python FastAPI + SQLAlchemy |
| Database | SQLite (file-based, lightweight) |
| AI/LLM | Groq API (free tier) with Llama 3.1 |
| RAG | scikit-learn TF-IDF vectorization |
| Hosting | Netlify (frontend) + Render (backend) |

## Project Structure

```
AI-Digital-Twin/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/       # ChatWindow, MessageBubble, FeedbackModal
│   │   ├── hooks/            # useChat custom hook
│   │   └── styles/           # CSS styles
│   └── package.json
├── backend/                  # Python FastAPI server
│   ├── api/                  # REST endpoints
│   ├── core/                 # AI pipeline (RAG, LLM, guardrails, identity)
│   ├── config/               # System prompt + model settings (owner customizes)
│   ├── data/                 # Training text files (owner customizes)
│   └── db/                   # SQLite database models
├── ARCHITECTURE.md           # Technical documentation
├── CLAUDE.md                 # AI assistant instructions
└── README.md                 # This file
```

## How It Works

1. **User sends a message** through the chat interface
2. **Identity Detection** checks if user is a recognized friend/family
3. **Input Guardrails** block inappropriate or manipulative queries
4. **RAG Retrieval** finds relevant info from training data (TF-IDF)
5. **LLM Generates** a response using personality prompt + context
6. **Output Guardrails** filter fabrications and negative statements
7. **Response displayed** to user with typing animation

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_api_key_here" > .env

# Run server
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs at `http://localhost:5173`

## Configuration

### Training Data (`backend/data/`)
Add `.txt` files with personal information:
- `hobbies.txt` - Interests and hobbies
- `personality.txt` - Communication style, values
- `interview_responses.txt` - Common Q&A responses
- `family_and_friends.txt` - Relationships (enables identity detection)
- `opinions.txt` - Views on various topics

### System Prompt (`backend/config/system_prompt.txt`)
Defines the AI's identity, tone, and behavior.

### Model Settings (`backend/config/settings.txt`)
```
temperature=0.7
max_tokens=500
history_limit=20
rag_top_k=3
```

## Deployment

### Frontend (Netlify)
1. Connect GitHub repo to Netlify
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Environment variable: `VITE_API_URL=https://your-backend.onrender.com`

### Backend (Render)
1. Connect GitHub repo to Render
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Environment variables:
   - `GROQ_API_KEY` - Your Groq API key
   - `ALLOWED_ORIGINS` - Frontend URL (for CORS)
   - `CHAT_ENABLED` - Kill switch (default: true)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message, get AI response |
| POST | `/api/feedback` | Submit thumbs up/down feedback |
| POST | `/api/analytics` | Track visit/message events |
| GET | `/api/health` | Health check + kill switch status |
| GET | `/docs` | Interactive API documentation |

## Security

- **Rate Limiting**: 30 requests/minute per IP
- **Jailbreak Protection**: Blocks prompt injection attempts
- **Manipulation Detection**: Detects social engineering
- **Topic Blocking**: Politics, religion, financial info
- **Output Filtering**: Prevents fabrication and negative statements
- **Kill Switch**: Disable chat via environment variable

## License

Private project - not for redistribution.
