# Muse — Creative Studio Agent

Muse is a multi-media, news-aware creative agent built on the [Google Agent
Development Kit (ADK)](https://google.github.io/adk-docs/). It's a
single-agent studio that writes stories, poems, scripts, and copy directly;
reports real local, international, and sports news; grounds speculation
about the future of AI and other fields in real recent developments; and
produces accompanying **images** and **spoken narration** on request — the
same pattern as the CodeQuest Academy demo, extended from one creative tool
(mission images) into a full text + news + image + audio toolkit.

## Features

- Native creative writing (stories, poems, scripts, brainstorms, copy) —
  no tool call needed, it's just the model thinking out loud
- `get_local_news` — real, current Sri Lanka / Colombo headlines
- `get_international_news` — real, current world headlines (BBC, Al
  Jazeera, Reuters, CNN)
- `get_sports_news` — real, current sports headlines
- `get_field_updates` — real recent developments in AI or any other field,
  used to ground forward-looking creative speculation ("what might happen
  next") in fact rather than invention
- `generate_image` — turns a prompt into a PNG, saved as an ADK session artifact
- `generate_narration` — turns a script, poem, or news summary into
  spoken-word audio (WAV), saved as an ADK session artifact, with a choice
  of 6 voices
- `suggest_creative_direction` — a small curated library of moods, visual
  language, and narration voices (cinematic, whimsical, noir, minimalist,
  epic-fantasy) Muse can ground a vague brief in

All four categories work together — e.g. ask for a news summary, an
illustration for it, and a spoken read-aloud in one request.

## Project structure

```
.
├── creative_studio_agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── news.py
│   └── trends.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Prerequisites

- Python 3.10 or newer
- A Google AI Studio API key, or a configured Vertex AI project
- Access to an image-capable and a TTS-capable Gemini model on your account
- A free [NewsAPI.org](https://newsapi.org) API key for the news and
  field-update tools

## Setup

1. Enter the project directory.

   ```
   cd creative_studio_agent
   ```

2. Create and activate a virtual environment.

   macOS/Linux:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell:
   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Install dependencies.

   ```
   python -m pip install -r requirements.txt
   ```

4. Create your local environment file and fill in your credentials.

   macOS/Linux:
   ```
   cp .env.example .env
   ```

   Windows PowerShell:
   ```
   Copy-Item .env.example .env
   ```

   Edit `.env` and provide either `GOOGLE_API_KEY` (AI Studio) or your
   Vertex AI project settings. Never commit this file.

   Model names in `.env.example` are placeholders — swap in whatever
   image-capable and TTS-capable Gemini model names your account currently
   has access to.

## Run the agent

From the repository root, with the virtual environment active:

```
adk web
```

Open the local URL printed by ADK and select `creative_studio_agent`.

## Example prompts

Pure creative writing (no tools involved):

- "Write me a short noir-style detective story, three paragraphs."
- "Give me five taglines for a coffee brand that only sells at night."
- "Brainstorm a fantasy world where music is currency."

Ground a brief with a creative direction:

- "Suggest a whimsical creative direction, then write a bedtime story in it."
- "Give me a noir direction and use it for a 60-second radio ad script."

Generate images:

- "Illustrate a lighthouse keeper meeting a sea dragon, in a 16:9 cinematic style."
- "Make a square minimalist poster for a jazz festival called Bluenote."
- "Generate a vertical epic-fantasy poster of a city built into a mountain."

Generate narration:

- "Narrate that detective story opening in the Charon voice, tense and urgent."
- "Read the tagline options aloud in a bright, playful voice."

Combine all three:

- "Write a 4-line poem about the first snow, illustrate it, and narrate it
  in a soft, warm voice."

News:

- "What's the latest local news in Colombo?"
- "Give me today's top international headlines."
- "Any Sri Lanka cricket news?"
- "Summarize the world news and illustrate the top story."

Future speculation, grounded in real updates:

- "What's happening in AI right now, and where do you think it's headed
  in the next year?"
- "Pull recent space exploration news and write a short speculative-fiction
  scene set five years from now, based on it."
- "What are the latest updates in climate tech? Narrate a short forecast."

## How it works

[`creative_studio_agent/agent.py`](creative_studio_agent/agent.py) wires
together a curated library of creative directions and seven function tools
around a single `root_agent`:

- `suggest_creative_direction` looks up (or lists) mood/style presets.
- `generate_image` calls a Gemini image model and saves the result as an
  ADK session artifact.
- `generate_narration` calls a Gemini TTS model, wraps the raw PCM audio in
  a WAV container, and saves it as an ADK session artifact.
- `get_local_news`, `get_international_news`, and `get_sports_news`
  ([`creative_studio_agent/news.py`](creative_studio_agent/news.py)) call
  NewsAPI.org — local news uses the `/everything` endpoint with a Sri
  Lanka / Colombo query (NewsAPI's `/top-headlines` doesn't support the
  `lk` country code), while international and sports use `/top-headlines`.
- `get_field_updates`
  ([`creative_studio_agent/trends.py`](creative_studio_agent/trends.py))
  fetches recent real coverage of a field (AI, science, space, etc.) so
  Muse's "what happens next" speculation is built on real, sourced ground
  rather than invented from nothing.

Muse is instructed to do all actual writing itself, reach for tools only
when the output needs to be seen, heard, or based on real current
information, and to clearly separate sourced facts from its own creative
speculation — keeping the creative voice consistent while staying honest
about what's real news versus what's Muse's own forecast.

## Extension ideas

- Add a `generate_music_brief` tool that drafts a structured prompt for an
  external music-generation service.
- Add sub-agents (e.g. a dedicated "Editor" agent) and delegate revision
  passes to them via ADK's multi-agent transfer.
- Cache NewsAPI responses briefly to stay well under the free-tier rate
  limit during a busy session.
- Persist generated artifacts to cloud storage instead of session-local
  storage so a project can be resumed across sessions.
- Add a tool that assembles a finished news summary + image + narration
  into a single shareable "briefing" artifact.
- Swap in live Gemini Live voice (real-time spoken conversation) instead of
  turn-by-turn narration, if you want a true voice agent later.

## Security

Keep API keys and cloud credentials only in your local `.env` file or a
secure secret manager. If a secret is ever committed, revoke or rotate it
before removing it from Git history.
