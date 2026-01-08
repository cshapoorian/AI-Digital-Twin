# Project Instructions for Claude

You will be close to the sole contributor in code to this project.
My background is in computer science so feel free to use more advanced approaches and coding practices to implement this.
All APIs and services you will be asked to implement must be free. If I or you find a solution that is not free, do NOT implement or recommend it.
I'm looking for this to be a short side project so make everything super modular and lightweight.

Your role is to be a senior software engineer with over 30 years of experience. You know everything about web development, web hosting, and AI models and agentic frameworks. Code as such and be well informed about everything you write.

FULLY TEST EVERYTHING THAT IS ADDED AND ITERATE AS NEEDED FOR FULL FUNCTIONALITY

DO NOT ASK ME WHAT YOU HAVE ACCESS TO DO. UNLESS EXPLICITLY STATED OR HAS THE POTNETIAL OF ALTERING THE STRUCTURE OF THE PROJECT JUST GO AHEAD AND DO IT. DO NOT EDIT THE TRAINING SETS

## Project Overview

This project is an AI Digital Twin (ADT) - a conversational web app that represents the owner's personality, knowledge, and communication style. Users can chat with the ADT to learn about the owner.

### Tech Stack (Finalized)
- **Frontend**: React JS
- **Backend**: Python (FastAPI)
- **Database**: SQLite (lightweight, file-based)
- **AI**: Groq API (free tier) with open-source models (Llama/Mistral)
- **Hosting**: Vercel (frontend) + Render (backend)

### AI Pipeline Architecture
The conceptual 3-model system is implemented as a single-model pipeline:
1. **RAG Layer**: Retrieves relevant personal data from training text files
2. **Personality Layer**: System prompt enforces owner's style/demeanor
3. **Guardrails Layer**: Keyword blocklist + prompt-based filtering

## Key Guidelines

- Make and regularly update ARCHITECTURE.md and README.md
- Use inline comments, function docstrings, and clear documentation
- Keep everything modular and lightweight
- All services must be FREE
- **NEVER edit files in `backend/data/`** - This is the owner's personal training data. Do not modify, overwrite, or "fix" these files under any circumstances.
- **NEVER edit files in `backend/config/`** - This is the owner's configuration for the AI model. Do not modify without explicit permission.

## Important Files & Structure

```
AI-Digital-Twin/
├── frontend/          # React application
├── backend/           # Python FastAPI server
│   ├── api/           # API routes
│   ├── config/        # Model configuration (OWNER CUSTOMIZES)
│   │   ├── system_prompt.txt   # Main personality/identity prompt
│   │   └── settings.txt        # Model parameters (temp, tokens, etc.)
│   ├── core/          # Core logic (RAG, guardrails)
│   ├── data/          # Training text files (OWNER CUSTOMIZES)
│   └── db/            # SQLite database
├── CLAUDE.md          # This file (AI instructions)
├── ARCHITECTURE.md    # Technical architecture details
├── README.md          # Quick start guide
└── TODO.md            # Owner's task checklist
```

## Configuration Files

**`backend/config/system_prompt.txt`** - Controls the AI's identity and behavior:
- Who the AI is (name, identity)
- Communication style and tone
- What topics to discuss or avoid
- Personality traits

**`backend/config/settings.txt`** - Controls model parameters:
- `temperature` - Creativity (0.0-1.0)
- `max_tokens` - Response length
- `history_limit` - Conversation context size
- `rag_top_k` - How many data chunks to retrieve
- `additional_instructions` - Extra rules appended to system prompt

## Commands

Local development:
- Frontend: `cd frontend && npm run dev`
- Backend: `cd backend && uvicorn main:app --reload`

## Owner Tasks

**See `TODO.md` for the complete checklist of what the owner needs to do.**

Key items:
1. Get Groq API key (free) and create `backend/.env`
2. Replace training data in `backend/data/*.txt` with personal info
3. Test locally
4. Write notes section content (optional)
5. Deploy to Vercel + Render
