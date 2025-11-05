# openai_service.py
import json
import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # library not installed; keep module import-safe
    OpenAI = None  # type: ignore

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


class OpenAIService:
    """
    Minimal wrapper for generating compact market blurbs.
    - Does NOT crash if no key or client.
    - Uses Responses API, robust text extraction.
    """

    def __init__(self) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        self.enabled = bool(api_key and OpenAI)
        self.client = OpenAI(api_key=api_key) if self.enabled else None

    def summarize_market(self, matchup: str, probability: Optional[float],
                         volume_24h: Optional[int]) -> str:
        prob_txt = f"{probability*100:.1f}%" if probability is not None else "N/A"
        vol_txt = f"{volume_24h:,}" if volume_24h is not None else "N/A"

        if not self.enabled:
            return f"{matchup}: implied {prob_txt}, 24h vol {vol_txt}."

        prompt = (
            "You are a concise NFL market analyst. Using only the provided numbers, write <=80 words:\n"
            "• State the matchup.\n"
            "• Give implied probability and 24h volume context.\n"
            "• Mention any large bid/ask gap briefly if present.\n"
            "Neutral tone. Do not invent numbers.")
        payload = {
            "matchup": matchup,
            "implied_prob": probability,
            "volume_24h": volume_24h
        }

        try:
            rsp = self.client.responses.create(
                model=DEFAULT_MODEL,
                input=[
                    {
                        "role": "system",
                        "content": "Be precise; do not invent numbers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload)
                    },
                ],
                max_output_tokens=180,
                temperature=0.2,
            )
            # Robust extraction across client versions
            text = getattr(rsp, "output_text", "") or ""
            if not text:
                try:
                    text = rsp.output[0].content[0].text
                except Exception:
                    text = ""
            return text.strip(
            ) or f"{matchup}: implied {prob_txt}, 24h vol {vol_txt}."
        except Exception:
            return f"{matchup}: implied {prob_txt}, 24h vol {vol_txt}."
