"""Muse: a multi-media, news-aware creative studio agent built on the
Google ADK.

Muse writes stories, poems, scripts, and copy directly (that's native LLM
behaviour and needs no tool), and reaches for function tools whenever a
request needs something the chat model can't produce, or know, on its own:

- generate_image          -> Gemini image model, saved as a PNG artifact
- generate_narration       -> Gemini TTS model, saved as a WAV artifact
- get_local_news            -> real Sri Lanka / Colombo headlines (NewsAPI)
- get_international_news    -> real world headlines (NewsAPI)
- get_sports_news            -> real sports headlines (NewsAPI)
- get_field_updates           -> real recent AI/tech/science/etc. developments,
                                  used to ground forward-looking speculation
- suggest_creative_direction   -> a small curated library of moods/styles

News and field-update tools return real, sourced articles. "What might
happen next" speculation is Muse's own creative extrapolation built on top
of that real grounding — never presented as if it were itself reported news.
"""

import io
import mimetypes
import os
import wave

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.genai import Client, types

from .news import get_international_news, get_local_news, get_sports_news
from .trends import get_field_updates

# ---------------------------------------------------------------------------
# Client + model configuration
# ---------------------------------------------------------------------------

_client = Client()

TEXT_MODEL = os.getenv("CREATIVE_TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.getenv("CREATIVE_IMAGE_MODEL", "gemini-3.1-flash-image")
TTS_MODEL = os.getenv("CREATIVE_TTS_MODEL", "gemini-2.5-flash-preview-tts")

# A small, curated library of creative directions Muse can offer when a
# brief is open-ended. Extend this freely — it's just structured data.
CREATIVE_DIRECTIONS = {
    "cinematic": {
        "mood": "Sweeping, high-contrast, emotionally charged",
        "visual_cues": "dramatic lighting, wide shots, shallow depth of field",
        "voice": "measured, resonant, deliberate pacing",
    },
    "whimsical": {
        "mood": "Playful, light, a little surreal",
        "visual_cues": "soft pastels, rounded shapes, exaggerated proportions",
        "voice": "bright, quick, curious",
    },
    "noir": {
        "mood": "Moody, mysterious, morally ambiguous",
        "visual_cues": "hard shadows, rain-slicked streets, muted color",
        "voice": "low, dry, unhurried",
    },
    "minimalist": {
        "mood": "Calm, restrained, precise",
        "visual_cues": "negative space, clean lines, a single focal point",
        "voice": "soft, even, few words",
    },
    "epic-fantasy": {
        "mood": "Grand, mythic, larger than life",
        "visual_cues": "vast landscapes, ornate detail, dramatic skies",
        "voice": "rich, theatrical, building intensity",
    },
}

# Voices available on the Gemini TTS model this agent targets.
AVAILABLE_VOICES = [
    "Kore", "Puck", "Charon", "Fenrir", "Aoede", "Zephyr",
]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def suggest_creative_direction(theme: str) -> dict:
    """Look up a curated creative direction (mood, visual language, and
    narration voice) for a theme, to ground a brief before generating media.

    Args:
        theme: A style keyword, e.g. "cinematic", "whimsical", "noir",
            "minimalist", or "epic-fantasy". Case-insensitive; partial
            matches fall back to the full catalogue.

    Returns:
        A dict with either the matching direction or the full catalogue
        of available directions if no match is found.
    """
    key = theme.strip().lower()
    if key in CREATIVE_DIRECTIONS:
        return {"status": "success", "theme": key, "direction": CREATIVE_DIRECTIONS[key]}
    return {
        "status": "not_found",
        "message": f"No preset for '{theme}'. Here is the full catalogue instead.",
        "available_directions": CREATIVE_DIRECTIONS,
    }


def generate_image(
    prompt: str,
    tool_context: ToolContext,
    aspect_ratio: str = "1:1",
    style: str = "",
) -> dict:
    """Generate an image from a text prompt and save it as a session artifact.

    Args:
        prompt: A vivid, detailed description of the image to create.
        aspect_ratio: One of "1:1", "16:9", "9:16", "4:3", "3:4".
        style: Optional style modifier appended to the prompt
            (e.g. "watercolor", "cinematic photograph", "flat vector art").

    Returns:
        A dict with status, the artifact filename, and a short summary.
    """
    full_prompt = f"{prompt}. Style: {style}." if style else prompt
    full_prompt += f" Aspect ratio {aspect_ratio}."

    try:
        response = _client.models.generate_content(
            model=IMAGE_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        image_bytes = None
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/png"
                break

        if image_bytes is None:
            return {"status": "error", "message": "No image data returned by the model."}

        ext = mimetypes.guess_extension(mime_type) or ".png"
        filename = f"muse_image_{abs(hash(prompt)) % 100000}{ext}"

        artifact = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename, artifact)

        return {
            "status": "success",
            "filename": filename,
            "summary": f"Generated a {aspect_ratio} image for: {prompt[:80]}",
        }
    except Exception as exc:  # surface a clean message back to the model
        return {"status": "error", "message": str(exc)}


def _pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = 24000) -> bytes:
    """Wrap raw 16-bit PCM audio in a standard WAV container."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return buffer.getvalue()


def generate_narration(
    text: str,
    tool_context: ToolContext,
    voice: str = "Kore",
    tone: str = "",
) -> dict:
    """Turn a script or passage into spoken-word narration and save it as a
    session artifact (WAV audio).

    Args:
        text: The text to narrate. Keep it to a paragraph or two per call.
        voice: One of Kore, Puck, Charon, Fenrir, Aoede, Zephyr.
        tone: Optional delivery note, e.g. "warm and reassuring",
            "tense and urgent", "playful".

    Returns:
        A dict with status, the artifact filename, and a short summary.
    """
    if voice not in AVAILABLE_VOICES:
        voice = "Kore"

    styled_text = f"Say this {tone}: {text}" if tone else text

    try:
        response = _client.models.generate_content(
            model=TTS_MODEL,
            contents=styled_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            ),
        )

        pcm_bytes = None
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                pcm_bytes = part.inline_data.data
                break

        if pcm_bytes is None:
            return {"status": "error", "message": "No audio data returned by the model."}

        wav_bytes = _pcm_to_wav_bytes(pcm_bytes)
        filename = f"muse_narration_{abs(hash(text)) % 100000}.wav"

        artifact = types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")
        tool_context.save_artifact(filename, artifact)

        return {
            "status": "success",
            "filename": filename,
            "voice": voice,
            "summary": f"Narrated {len(text)} characters with the {voice} voice.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# ---------------------------------------------------------------------------
# Root agent
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="muse",
    model=TEXT_MODEL,
    description=(
        "A creative studio agent that writes stories, poems, and scripts; "
        "reports real local, international, and sports news; and generates "
        "accompanying images and spoken narration."
    ),
    instruction="""
You are Muse, an imaginative creative director, news desk, and futures
thinker in one.

## Creative writing
TEXT (stories, poems, scripts, ad copy, world-building, brainstorms) is
something you write yourself, directly in the conversation. Never call a
tool for plain writing -- that's your native strength.

If a brief is vague or the user asks for inspiration, call
`suggest_creative_direction` with a style keyword to ground your writing
and prompts in a concrete mood, visual language, and narration voice --
then build on that rather than asking the user to decide everything
themselves.

## Images
When the user wants to SEE something (an illustration, concept art, a
scene, a poster, a badge, a mood board image, a news-story illustration),
call `generate_image`. Write a vivid, specific prompt yourself before
calling it -- don't just forward the user's raw request if it's vague.

## Narration
When the user wants to HEAR something (narration of a script or poem, a
voiceover, a news read-aloud), call `generate_narration`. Keep each call
to a paragraph or two; split long scripts or news summaries into multiple
calls.

## News
When the user asks about current events, always use a news tool rather
than your own knowledge -- you do not know today's news:
- `get_local_news` for Sri Lanka / Colombo news
- `get_international_news` for world news
- `get_sports_news` for sports
Pick the right one(s) based on what's asked; if it's ambiguous, ask which
they mean or check more than one. Summarize the returned articles in your
own words, always naming the source and roughly when it was published, and
mention you can pull the full article at its URL if they want more. If a
tool returns a NEWS_API_KEY error, tell the user plainly that news isn't
configured yet rather than making anything up.

## Future speculation ("what's coming")
When the user asks what might happen next, or wants creative speculation
about the future of AI or another field, call `get_field_updates` first to
ground yourself in real, recent, sourced developments. Then build your own
clearly-labeled creative extrapolation on top of that -- explicitly mark
the shift from "here's what's actually happening" (sourced) to "here's
where I think this could be headed" (your speculation). Never blur the two
or present a guess as a fact.

## General
Always be genuinely creative: offer a strong, specific first take rather
than a bland or generic one, and briefly explain the creative choices you
made (mood, style, structure) so the user can steer you.

When you generate an image or narration, or report news, tell the user
what you found or made and why, in plain, warm language -- don't describe
your tool call mechanics.
""",
    tools=[
        generate_image,
        generate_narration,
        suggest_creative_direction,
        get_local_news,
        get_international_news,
        get_sports_news,
        get_field_updates,
    ],
)
