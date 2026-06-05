"""
Single-image classifier via OpenRouter Vision API (OpenAI-compatible).
Returns category + confidence score for review-queue routing.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI

log = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "hero", "before_after", "installation", "product",
    "lifestyle", "exterior", "interior", "text_overlay",
    "portrait", "reject",
}

_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

# Confidence thresholds for review queue routing
CONFIDENCE_AUTO   = 0.82   # >= auto-file
CONFIDENCE_REVIEW = 0.55   # < this → route to review/

_PROMPT = """You are a strict photo classifier for a home services photo bank (security, HVAC, solar, roofing, bathroom, etc.).

Classify the image into EXACTLY ONE of these categories:

CATEGORY DEFINITIONS (read carefully):

hero         — Full-width marketing banner. MUST be landscape (wider than tall), high quality, no dominant person. A banner WITH small text overlay is still hero.
before_after — ONE image showing the SAME subject in two states side-by-side or split (old vs new, dirty vs clean). A person shaking hands, greeting a customer, or a sales scene is NOT before_after.
installation — Technician/worker actively installing, mounting, wiring, or servicing equipment. KEY SIGNALS: visible tools, drill holes, exposed wires, ladder, worker's hands on device, unfinished mounting. A device neatly mounted on a wall with no worker = interior, NOT installation.
product      — Equipment or product isolated on a CLEAN, plain, or studio background (white/grey/gradient). The product is the ONLY subject. If a room, wall, furniture, or person is visible around it → interior or lifestyle, NOT product.
lifestyle    — People in a home or office naturally using or benefiting from a product. Real people, real environment. NOT: staff headshots, CCTV grid screens, app screenshots, phone UI demos, or illustrations.
exterior     — Outside view of a residential or commercial building. Aerial/drone views count.
interior     — Inside view of a room (living room, kitchen, hallway, office). The ROOM is the subject. A device neatly mounted/installed in a finished room = interior. If a worker or tools are present → installation instead.
text_overlay — A real photo that has large overlaid text, a watermark, a caption bar, or an infographic frame covering significant area.
portrait     — A single person headshot or cut-out staff photo. NOT lifestyle (no home context).
reject       — Logo, icon, illustration, map, color swatch, UI screenshot, CCTV grid, app interface, social media graphic. NOT a real-world photo.

PRIORITY RULES (when two categories fit, use the higher one):
1. reject > all others (if it's a graphic/UI, always reject)
2. portrait > lifestyle (single headshot without home = portrait)
3. installation > interior/product (if worker+tools present)
4. text_overlay only if overlay dominates; underlying photo still gets the photo category as runner_up

Respond in JSON only:
{"category": "<name>", "confidence": <0.0-1.0>, "runner_up": "<name>", "reason": "<max 8 words>"}"""


@dataclass
class ClassifyResult:
    category: str
    confidence: float
    runner_up: str
    reason: str


class VisionClient:
    def __init__(self, api_key: str, model: str, fallback_model: str = ""):
        self.model = model
        self.fallback_model = fallback_model or model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    async def classify(self, image_path: Path) -> ClassifyResult:
        """
        Classify a single image file.
        Returns ClassifyResult with category, confidence, runner_up, reason.
        Falls back to unknown/0.0 on total failure.
        """
        data = image_path.read_bytes()
        mime = _MIME.get(image_path.suffix.lower(), "image/jpeg")
        b64 = base64.b64encode(data).decode()

        models = [self.model]
        if self.fallback_model != self.model:
            models.append(self.fallback_model)

        last_error: Exception | None = None
        for model in models:
            try:
                response = await self._client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _PROMPT},
                            {"type": "image_url",
                             "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        ],
                    }],
                    max_tokens=80,
                    temperature=0,
                )
                raw = response.choices[0].message.content.strip()
                return _parse_response(raw, image_path.name)
            except Exception as e:
                last_error = e
                log.warning("classify failed (model=%s, file=%s): %s",
                            model, image_path.name, e)
                continue

        log.error("All models failed for %s: %s", image_path.name, last_error)
        return ClassifyResult("unknown", 0.0, "unknown", "api error")


def _parse_response(raw: str, filename: str) -> ClassifyResult:
    """Parse JSON response from model. Falls back gracefully."""
    # Strip markdown code blocks if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        data = json.loads(text)
        category = str(data.get("category", "unknown")).lower().strip()
        if category not in VALID_CATEGORIES:
            # fuzzy match
            for cat in VALID_CATEGORIES:
                if cat in category:
                    category = cat
                    break
            else:
                category = "unknown"
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        runner_up = str(data.get("runner_up", "unknown")).lower().strip()
        reason = str(data.get("reason", ""))[:60]
        return ClassifyResult(category, confidence, runner_up, reason)
    except Exception:
        # Fallback: try to extract category name from raw text
        log.warning("JSON parse failed for %s, raw: %s", filename, raw[:80])
        for cat in VALID_CATEGORIES:
            if cat in raw.lower():
                return ClassifyResult(cat, 0.5, "unknown", "parse fallback")
        return ClassifyResult("unknown", 0.0, "unknown", "parse error")
