import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)

# Rate limiting: protects your API quota/cost once this is public. Adjust the
# number to taste -- 15/hour is generous for one person testing, but keeps a
# stranger from hammering the endpoint and burning through your free tier.
limiter = Limiter(get_remote_address, app=app, default_limits=[])


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests -- please wait a bit and try again."}), 429

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# Mock mode: if there's no API key yet, the app still works end-to-end using
# this canned response, so you can build/test the whole UI without a key.
MOCK_MODE = not bool(GEMINI_API_KEY)

client = None
if not MOCK_MODE:
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are an experienced, kind but honest college admissions essay editor.
You give high school students concrete, specific feedback on personal statements and
supplemental essays -- the kind of feedback a great writing teacher gives, not generic praise.

Return ONLY valid JSON, no markdown code fences, no preamble, matching exactly this schema:

{
  "structure_feedback": string (2-3 sentences on the essay's structure and narrative arc),
  "prompt_alignment": {"score": integer 1-5, "explanation": string (1-2 sentences)},
  "voice_feedback": string (2-3 sentences on whether the voice sounds genuine and specific to this writer),
  "cliches": [ {"quote": string, "why": string} ],
  "show_dont_tell": [ {"quote": string, "suggestion": string} ],
  "strengths": [ string ] (2-4 short specific things that genuinely work)
}

Rules:
- "quote" fields MUST be exact verbatim substrings copied character-for-character from the
  essay draft provided, so they can be located in the original text. Never paraphrase a quote.
- Keep every explanation short, specific, and actionable -- reference what THIS essay actually
  does, never generic advice.
- cliches and show_dont_tell can be empty arrays if genuinely not present -- do not invent issues.
- Limit cliches and show_dont_tell to at most 5 items each, the most important ones.
"""


def mock_feedback(essay: str) -> dict:
    """Canned response so the UI can be built/tested without a real API key."""
    first_sentence = essay.strip().split(".")[0][:60] if essay.strip() else "your opening line"
    return {
        "structure_feedback": (
            "[MOCK DATA] Your essay opens with a concrete moment, which is good, but the "
            "middle section moves through several ideas quickly -- consider spending more "
            "time on the one that matters most."
        ),
        "prompt_alignment": {
            "score": 4,
            "explanation": "[MOCK DATA] The essay connects to the prompt but the link could be more explicit in your conclusion.",
        },
        "voice_feedback": (
            "[MOCK DATA] Your voice comes through clearly in a few places, but some sentences "
            "sound more formal than how you actually talk -- trust the more casual version."
        ),
        "cliches": [
            {
                "quote": first_sentence if first_sentence else "example phrase",
                "why": "[MOCK DATA] This is a placeholder cliche flag -- replace GEMINI_API_KEY with a real key to get feedback on your actual text.",
            }
        ],
        "show_dont_tell": [
            {
                "quote": "[MOCK DATA] example quote",
                "suggestion": "[MOCK DATA] Placeholder suggestion -- real feedback appears once your API key is set.",
            }
        ],
        "strengths": [
            "[MOCK DATA] This is a placeholder strength.",
            "[MOCK DATA] Add your real GEMINI_API_KEY to .env to get real feedback.",
        ],
    }


@app.route("/")
def home():
    return render_template("index.html", mock_mode=MOCK_MODE)


@app.route("/api/feedback", methods=["POST"])
@limiter.limit("5 per hour")
def feedback():
    data = request.get_json(force=True) or {}
    essay = (data.get("essay") or "").strip()
    prompt_text = (data.get("prompt") or "").strip()
    word_limit = data.get("wordLimit")

    if not essay:
        return jsonify({"error": "Paste your essay draft first."}), 400

    word_count = len(essay.split())

    if MOCK_MODE:
        result = mock_feedback(essay)
    else:
        user_message = (
            f"College application prompt:\n{prompt_text or '(not provided)'}\n\n"
            f"Word limit: {word_limit or '(not provided)'}\n"
            f"Actual word count: {word_count}\n\n"
            f"Essay draft:\n\"\"\"\n{essay}\n\"\"\"\n"
        )
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_message,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                },
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            return jsonify({"error": "Could not parse the model's feedback. Please try again."}), 502
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": f"API error: {str(e)}"}), 502

    result["word_count"] = {"count": word_count}
    if word_limit:
        try:
            limit_val = int(word_limit)
            result["word_count"]["limit"] = limit_val
            if word_count > limit_val:
                status = "over"
            elif word_count < limit_val * 0.8:
                status = "short"
            else:
                status = "good"
            result["word_count"]["status"] = status
        except (TypeError, ValueError):
            pass

    return jsonify(result)


if __name__ == "__main__":
    if MOCK_MODE:
        print("Running in MOCK MODE - no GEMINI_API_KEY found in .env. Feedback will be placeholder data.")
    app.run(debug=True, port=5000)
