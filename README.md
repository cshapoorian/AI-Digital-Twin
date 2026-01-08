# AI Digital Twin

A conversational web application that serves as an AI representation of its owner. Users can chat with the digital twin to learn about the owner's interests, background, and perspectives.

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- Groq API key (free at https://console.groq.com)

### Setup

1. **Clone and install dependencies**

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

2. **Configure environment**

```bash
# backend/.env
GROQ_API_KEY=your_groq_api_key_here
ALLOWED_ORIGINS=http://localhost:5173
CHAT_ENABLED=true
```

3. **Add your training data**

Add text files to `backend/data/` describing yourself:
- `personality.txt` - Your communication style, mannerisms
- `hobbies.txt` - Your interests and hobbies
- `resume.txt` - Professional background
- `hottakes.txt` - Your opinions (non-controversial)

4. **Run locally**

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

5. **Open** http://localhost:5173

## Project Structure

```
AI-Digital-Twin/
├── frontend/              # React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   └── styles/        # CSS styles
│   └── package.json
├── backend/               # Python FastAPI server
│   ├── api/               # API routes
│   ├── core/              # AI pipeline (RAG, LLM, guardrails)
│   ├── data/              # Training text files
│   ├── db/                # SQLite database
│   └── requirements.txt
├── ARCHITECTURE.md        # Technical documentation
├── CLAUDE.md              # AI assistant instructions
└── README.md              # This file
```

## How It Works

1. **User sends a message** through the chat interface
2. **RAG retrieval** finds relevant information from your training data
3. **LLM generates** a response using your personality profile
4. **Guardrails filter** ensures the response is appropriate
5. **Response displayed** to the user

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed technical documentation.

## Deployment

### Frontend (Vercel)

1. Connect GitHub repo to Vercel
2. Set root directory to `frontend`
3. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`

### Backend (Render)

1. Connect GitHub repo to Render
2. Set root directory to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `GROQ_API_KEY`
   - `ALLOWED_ORIGINS=https://your-frontend.vercel.app`
   - `CHAT_ENABLED=true`

## Configuration

### Kill Switch

To temporarily disable the chat (e.g., during maintenance):

```bash
# Set in environment
CHAT_ENABLED=false
```

The chat will display a maintenance message instead of processing queries.

## Missing / TODO

- [ ] Owner needs to add training data files to `backend/data/`
- [ ] Owner needs to configure Groq API key
- [ ] Owner needs to write static notes content for the Notes section
- [ ] Deployment to Vercel/Render

## License

Private project - not for redistribution.
