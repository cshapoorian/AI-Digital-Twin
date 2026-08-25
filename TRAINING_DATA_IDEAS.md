# Training Data Ideas

A list of what would most improve the digital twin's authenticity, based on a full review of the current
`backend/data/*.txt` files. This is a reference for *you* to work from when you have time to add content —
nothing here is required, and none of it was added automatically (per the rule that training data is
owner-only).

## What's already strong

Don't second-guess these - they're genuinely good:
- `personality.txt` - communication style, common phrases ("yes dude", "bruh", "that's crazy"), sense of humor,
  values in conversation. This is exactly the kind of texture that makes the first-person voice land.
- `opinions.txt` - tech opinions, hot takes, food/lifestyle preferences with real specificity.
- `interview_responses.txt` - thorough coverage of standard interview questions with real detail, not generic
  answers.
- `hobbies.txt` - specific enough to sound real (exact snowboard tricks, exact anime titles, the Detroit:
  Become Human callout).

## 1. Time-sensitive info that may now be stale (check this first)

This is the highest-priority item because a stale fact is worse than a missing one - it actively misleads
people instead of just deflecting.

- `interview_responses.txt` says the Bland AI role ended "Oct - Nov 2025" due to layoffs, and "Why I Left My
  Last Position" describes being "eager to hit the ground running at my next role." It's now August 2026 -
  nearly 10 months later. If your job situation has changed since then (new role, still searching, went
  independent, etc.), the twin is currently telling recruiters outdated information about your availability.
  This is worth checking before anything else on this list.
- The "5 Year Plan" / career goals section may also be worth a fresh pass if your thinking has evolved.

## 2. Situational/reactive examples (biggest authenticity lever)

Right now the training data is mostly *facts about you* (what you did, what you like). What's missing is
*how you react* in the moment - which is what actually makes a first-person voice feel like a real person
instead of a well-informed narrator. A few examples in a new "How I React" style section would go a long way:

- How you respond to a compliment
- How you respond to being told you're wrong
- How you handle being put on the spot / an awkward silence
- A time you changed your mind about something after being challenged
- What actually annoys you in daily life (small stuff, not just work pet peeves)

## 3. More verbatim voice examples

`personality.txt` documents your phrases and mannerisms *descriptively* ("I might say 'yes dude'"), but a few
actual example exchanges - a short back-and-forth the way you'd really text or talk - would give the model
something to pattern-match against more directly than a description can. Even 3-4 short examples would help,
e.g.:

```
Someone: "hows it going"
You: "not bad man, just been [whatever's actually true lately]"
```

## 4. More stories with real texture

You've got two great ones already (the soccer goal with stitches, the bluetooth memory leak). Specific,
vivid stories are what make a conversation feel real instead of like a resume read aloud. A few more in any
category (work, sports, friends, travel, something that went wrong, something you're proud of outside work)
would diversify what the twin can pull from instead of reusing the same two anecdotes for every "tell me a
story" type question.

## 5. Current projects / what you're into right now

`hobbies.txt` mentions being excited about agentic systems and ML certifications - that's good, but it's
also the kind of thing that goes stale fast in AI. A quick pass every few months on "what I'm currently
learning/building/interested in" keeps the twin feeling like a living snapshot instead of a fixed point in
time from when you built this.

---

**How to use this**: pick whatever feels highest-value for your actual goals right now (if you're using this
for job searching, #1 and #2 probably matter most; if it's more of a "fun project to show people," #3 and #4
matter more). Add to the existing `.txt` files in `backend/data/` in the same style they're already written
in - the RAG retrieval will pick up new sections automatically next time the backend restarts (or via the
`reload_training_data()` path if you wire up a manual reload trigger).
