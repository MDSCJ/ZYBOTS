# Muse — Creative Studio Agent

Muse is a multi-media creative agent built on the [Google Agent Development
Kit (ADK)](https://google.github.io/adk-docs/). It's a single-agent studio
that writes stories, poems, scripts, and copy directly, and can produce
accompanying **images** and **spoken narration** on request — the same
pattern as the CodeQuest Academy demo, extended from one creative tool
(mission images) into a full text + image + audio toolkit.

## Features

- Native creative writing (stories, poems, scripts, brainstorms, copy) —
  no tool call needed, it's just the model thinking out loud
- `generate_image` — turns a prompt into a PNG, saved as an ADK session artifact
- `generate_narration` — turns a script or passage into spoken-word audio
  (WAV), saved as an ADK session artifact, with a choice of 6 voices
- `suggest_creative_direction` — a small curated library of moods, visual
  language, and narration voices (cinematic, whimsical, noir, minimalist,
  epic-fantasy) Muse can ground a vague brief in

## Project structure

```
.
├── creative_studio_agent/
│   ├── __init__.py
│   └── agent.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Prerequisites

- Python 3.10 or newer
- A Google AI Studio API key, or a configured Vertex AI project
- Access to an image-capable and a TTS-capable Gemini model on your account

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

## How it works

[`creative_studio_agent/agent.py`](creative_studio_agent/agent.py) defines
a curated library of creative directions and three function tools around a
single `root_agent`:

- `suggest_creative_direction` looks up (or lists) mood/style presets.
- `generate_image` calls a Gemini image model and saves the result as an
  ADK session artifact.
- `generate_narration` calls a Gemini TTS model, wraps the raw PCM audio in
  a WAV container, and saves it as an ADK session artifact.

Muse is instructed to do all actual writing itself and reach for tools only
when the output needs to be seen or heard — keeping the creative voice
consistent while still producing real media files.

## Extension ideas

- Add a `generate_music_brief` tool that drafts a structured prompt for an
  external music-generation service.
- Add sub-agents (e.g. a dedicated "Editor" agent) and delegate revision
  passes to them via ADK's multi-agent transfer.
- Persist generated artifacts to cloud storage instead of session-local
  storage so a project can be resumed across sessions.
- Add a tool that assembles a finished image + narration pair into a single
  shareable "creative brief" summary.

## Security

Keep API keys and cloud credentials only in your local `.env` file or a
secure secret manager. If a secret is ever committed, revoke or rotate it
before removing it from Git history.
