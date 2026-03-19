import requests, json, re, logging
from flask import current_app

logger   = logging.getLogger(__name__)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM = """You are an expert SQL developer.
Convert the user's plain English question into a correct SQL query.
Reply ONLY with valid JSON — no markdown, no code fences, no extra text.
The JSON must have exactly two keys: "sql" and "explanation"."""

def generate_sql(question: str, dialect: str = "MySQL") -> dict:
    key = current_app.config.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not set in .env file.")

    model = current_app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user",   "content":
                        f"SQL Dialect: {dialect}\n"
                        f"Question: {question}\n\n"
                        f'Respond ONLY with: {{"sql":"...","explanation":"..."}}'}
                ],
                "temperature": 0.1,
                "max_tokens": 1200,
            },
            timeout=30,
        )
        r.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Groq API timed out.")
    except requests.exceptions.HTTPError:
        try:    detail = r.json().get("error", {}).get("message", r.text)
        except: detail = r.text
        raise RuntimeError(f"Groq API error: {detail}")

    data = r.json()
    raw  = data["choices"][0]["message"]["content"].strip()
    raw  = raw.replace("```json","").replace("```","").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        parsed = json.loads(m.group(0)) if m else (_ for _ in ()).throw(
            RuntimeError("AI returned unexpected format."))

    return {
        "sql":         parsed.get("sql","").strip(),
        "explanation": parsed.get("explanation",""),
        "tokens_used": data.get("usage",{}).get("total_tokens",0),
        "model":       model,
    }