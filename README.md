# AI Digital Twin

A conversational web application that serves as an AI representation of its owner. Users can chat with the digital twin to learn about the owner's interests, background, and perspectives.

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
└── README.md              # This file
```

## How It Works

1. **User sends a message** through the chat interface
2. **RAG retrieval** finds relevant information from your training data
3. **LLM generates** a response using your personality profile
4. **Guardrails filter** ensures the response is appropriate
5. **Response displayed** to the user

## License

Private project - not for redistribution.
