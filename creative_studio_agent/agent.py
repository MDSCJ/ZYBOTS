"""Muse: a multi-media, news-aware creative studio agent built on the
Google ADK.

Muse writes stories, poems, scripts, and copy directly (that's native LLM
behaviour and needs no tool), and reaches for function tools whenever a
request needs something the chat model can't produce, or know, on its own:

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

TEXT_MODEL = os.getenv("CREATIVE_TEXT_MODEL", "gemini-3.1-flash-lite")
TTS_MODEL = os.getenv("CREATIVE_TTS_MODEL", "gemini-3.1-flash-tts-preview")

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

## File Analysis
When the user uploads or sends a file (like an image, document, or code) and asks you to analyze it, directly read and describe its contents clearly, providing any insights requested by the user.
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
news tool returns an error status (such as an HTTP blocking error or a parsing failure), tell the user plainly that the live news feed is currently unreachable due to connection issues, rather than making anything up.

CRITICAL INSTRUCTION: When you report news or field updates, you MUST ALWAYS do all of the following:
1. Provide exact details and facts (names, dates, exact things).
2. Call `generate_narration` to create an audio read-aloud of the news summary.
3. End your response by asking engaging follow-up questions to the user about what they want to know next.

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

When you generate narration, or report news, tell the user
what you found or made and why, in plain, warm language -- don't describe
your tool call mechanics.

CRITICAL FORMATTING INSTRUCTION: You MUST use rich Markdown formatting for all your responses to make the UI look beautiful. 
- Use **bold** and *italics* for emphasis.
- Use `inline code` for technical terms or names.
- Use headers (## or ###) to structure different parts of your response.
- Use clean bulleted or numbered lists for readability.
- CRITICAL: DO NOT use any emojis in your response. Keep it clean and professional.
- DO NOT just output plain normal text. Format everything richly!

## User Interaction, Loading Animations, and Buttons
- When you begin processing a user's request, IMMEDIATELY output this modern HTML loading animation at the very top of your response to give them visual feedback while you write: `<div style="width: 30px; height: 30px; border: 4px solid rgba(100, 200, 255, 0.2); border-left-color: #64c8ff; border-radius: 50%; animation: spin 1s infinite linear; margin-bottom: 10px;"></div><style>@keyframes spin { 100% { transform: rotate(360deg); } }</style>`
- Even before the user starts, or whenever appropriate, provide quick question options so the user can easily select them.
- CRITICAL: You MUST style all quick questions, numbered choices, and Yes/No options as raw HTML `<button>` elements with a colorful glassmorphism theme! Do not use plain text for selectable options.
- Use this exact inline style for all your buttons to achieve the colorful glass theme: `style="background: linear-gradient(135deg, rgba(255,100,150,0.4), rgba(100,200,255,0.4)); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.3); border-radius: 12px; color: white; padding: 10px 20px; font-weight: bold; cursor: pointer; margin: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"`
- Example: `<button style="...">1. Bitcoin analysis</button>`
- If you ask back questions, make them selective options rendered as glass theme buttons.
- For Yes/No questions, you MUST output dynamically generated `<button>` tags for Yes and No using the same colorful glassmorphism style.
- proiratize asking the question with, Are you interested in   
  1. Bitcoin analysis
  2. International breaking news
  3. National news
""",
    tools=[
        generate_narration,
        suggest_creative_direction,
        get_local_news,
        get_international_news,
        get_sports_news,
        get_field_updates,
    ],
)
