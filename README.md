# Draft Desk

An AI-assisted college essay feedback tool. Paste a personal statement or
supplemental essay and get margin-note-style feedback on structure, voice,
clichés, "show don't tell" moments, and whether the essay actually answers
the prompt.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open [open on render](https://draft-desk.onrender.com)

## Mock mode

If `.env` has no `GEMINI_API_KEY`, the app runs in **mock mode** automatically:
you get placeholder feedback (clearly labeled `[MOCK DATA]`) so you can build
and test the entire UI without an API key. Once you add a real key, mock mode
turns off by itself — no code changes needed.

## Adding a real Gemini API key

1. Go to https://aistudio.google.com, sign in with a Google account.
2. Click "Get API key" — no credit card required for the free tier.
3. Paste the key into `.env` as `GEMINI_API_KEY=...`.
4. Restart `python app.py`.

## Pushing to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Draft Desk MVP"
```

Then create an empty repo on github.com (no README/license, you already have
files), copy the commands it shows you (something like):

```bash
git remote add origin https://github.com/your-username/draft-desk.git
git branch -M main
git push -u origin main
```

`.gitignore` already excludes `.env` and `venv/`, so your key won't be
committed by accident -- but double check with `git status` before your
first commit that `.env` isn't listed as a tracked file.

## Rate limiting

The `/api/feedback` endpoint is limited to 5 requests/hour per visitor
(see `app.py`, uses Flask-Limiter). This protects your API quota/cost once
the app is public. Adjust the number in `app.py` if you want it looser or
stricter.

## Deploying to Render

1. Push this project to a GitHub repo (see steps above).
2. Go to render.com, sign in, click **New → Web Service**, connect your repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. In the **Environment** tab, add `GEMINI_API_KEY` and `GEMINI_MODEL` as
   environment variables (same values as your local `.env`) — never commit
   `.env` or hardcode the key in code.
6. Deploy. Render gives you a public URL like `your-app.onrender.com`.

## Roadmap ideas

- Save/compare multiple drafts
- Library of common supplemental prompts
- Highlight flagged quotes directly in the essay text
