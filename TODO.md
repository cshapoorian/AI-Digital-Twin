# AI Digital Twin - Owner Tasks

This file tracks what YOU (the owner) need to complete to finish the project.

---

## REQUIRED - Must Complete Before Launch

### 1. Get Groq API Key (5 minutes)
- [ ] Go to https://console.groq.com
- [ ] Create a free account
- [ ] Generate an API key
- [ ] Create `backend/.env` file (copy from `.env.example`)
- [ ] Add your API key: `GROQ_API_KEY=your_key_here`

### 2. Customize Training Data (30-60 minutes)
The example data in `backend/data/` contains placeholder content. Replace it with YOUR information.

| File | What to Write |
|------|--------------|
| `personality.txt` | Your communication style, common phrases, humor type, values |
| `hobbies.txt` | Your hobbies, interests, current obsessions, things you want to learn |
| `resume.txt` | Career path, skills, what you enjoy about work (keep it public-friendly) |
| `opinions.txt` | Non-controversial hot takes, food preferences, pet peeves |

**Tips:**
- Write naturally, as if explaining yourself to someone
- More detail = better AI responses
- Avoid placeholder text like "[your answer here]"
- Keep it factual and avoid controversial topics

### 3. Test Locally (10 minutes)
```bash
# Terminal 1 - Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and test the chat.

---

## OPTIONAL - Customization

### 4. Write Notes Section Content
Location: `frontend/src/components/NotesSection.jsx`

You mentioned wanting to write about why AI digital twins at scale could reduce human interaction. Edit the `NotesSection.jsx` file to add your thoughts.

### 5. Customize the Welcome Message
Location: `frontend/src/components/ChatWindow.jsx` (lines 25-34)

Update the `WelcomeMessage` component to personalize the greeting.

### 6. Adjust Guardrails (if needed)
Location: `backend/core/guardrails.py`

The default guardrails block:
- Politics, elections, political parties
- Religion and religious practices
- Sensitive social issues
- Personal info (salary, address, phone)
- Profanity

You can modify `BLOCKED_TOPICS` if you want to allow/block different topics.

### 7. Change the LLM Model
Location: `backend/.env`

Options (all free on Groq):
- `llama-3.1-8b-instant` - Fast, good quality (default)
- `llama-3.1-70b-versatile` - Higher quality, slower
- `mixtral-8x7b-32768` - Good for longer conversations

---

## DEPLOYMENT

### 8. Deploy Backend to Render
1. Create account at https://render.com
2. Connect your GitHub repo
3. Create new "Web Service"
4. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   - `GROQ_API_KEY` = your key
   - `ALLOWED_ORIGINS` = your Vercel URL (after step 9)
   - `CHAT_ENABLED` = true

### 9. Deploy Frontend to Vercel
1. Create account at https://vercel.com
2. Import your GitHub repo
3. Settings:
   - Root Directory: `frontend`
   - Framework Preset: Vite
4. Environment Variables:
   - `VITE_API_URL` = your Render backend URL (e.g., `https://your-app.onrender.com`)

### 10. Update CORS After Deployment
Go back to Render and update `ALLOWED_ORIGINS` to your Vercel URL.

---

## MAINTENANCE

### Disable Chat Temporarily
Set `CHAT_ENABLED=false` in Render environment variables.

### View Feedback/Unanswered Questions
The SQLite database stores feedback at `backend/db/adt.db`. You can:
- Download it from Render
- Use a SQLite viewer to see the `feedback` table
- Look for `feedback_type = 'unanswered'` to find questions to address

### Add New Training Data
1. Add/edit `.txt` files in `backend/data/`
2. Restart the backend (Render will auto-restart on deploy)

---

## Questions?

Check these files for technical details:
- `ARCHITECTURE.md` - System design and data flow
- `README.md` - Quick start guide
- `CLAUDE.md` - Project requirements and context
