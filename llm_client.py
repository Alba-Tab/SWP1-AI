import os
import json
import re
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from models import GenerateRequest, GenerateResponse
from prompt_builder import build_system_prompt, build_user_prompt

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("No se encontró OPENROUTER_API_KEY en .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

_MODEL        = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash")
_SITE_URL     = os.getenv("OPENROUTER_SITE_URL", "")
_SITE_NAME    = os.getenv("OPENROUTER_SITE_NAME", "")
_MAX_RETRIES  = 3
_DEFAULT_RETRY_WAIT = 15


def _parse_retry_seconds(error_msg: str) -> float:
    """Extrae el tiempo de espera sugerido por la API del mensaje de error 429."""
    match = re.search(r"retry[_ ]in\s+([\d.]+)s", error_msg, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1.0
    return _DEFAULT_RETRY_WAIT


def _extract_json(raw: str) -> str:
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw


async def generate_diagram(request: GenerateRequest) -> GenerateResponse:
    user = build_user_prompt(request)
    last_error = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": _SITE_URL,
                    "X-OpenRouter-Title": _SITE_NAME,
                },
                model=_MODEL,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user",   "content": user},
                ],
            )

            raw = _extract_json(response.choices[0].message.content)
            data = json.loads(raw)
            return GenerateResponse(**data)

        except Exception as e:
            last_error = e
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                wait = _parse_retry_seconds(error_str)
                print(f"[WARN] 429 quota exceeded (intento {attempt}/{_MAX_RETRIES}). "
                      f"Reintentando en {wait:.1f}s...")
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(wait)
                    continue
            raise
