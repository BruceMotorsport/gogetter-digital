#!/usr/bin/env python3
"""
GoGetter Writing Engine v1.0
AI-powered content generator for romance novels, business content, and technical writing.
Uses Groq API (free tier) with qwen/qwen3.2-30b model.

Usage:
    python writing_engine.py --genre romance --topic "A second-chance love story set in Paris" --words 5000
    python writing_engine.py --genre business --topic "Startup pitch deck narrative" --words 2000
    python writing_engine.py --genre technical --topic "API integration guide" --words 3000
    python writing_engine.py --genre blog --topic "Remote work productivity tips" --words 1500
    python writing_engine.py --genre fiction --topic "A cyberpunk detective mystery" --words 8000
    python writing_engine.py --genre all --topic "Complete romance novel package" --words 10000
"""

import os
import sys
import json
import time
import argparse
import textwrap
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GROQ_MODEL = "openai/gpt-oss-20b"      # Primary: no thinking overhead, fast, 131K context
GROQ_FALLBACK = "qwen/qwen3.6-27b"     # Fallback: use reasoning_effort=none to avoid token waste
GROQ_THINKING_MODEL = "qwen/qwen3.6-27b"  # Qwen with thinking disabled
WORDS_PER_CHUNK = 800                    # Words to request per generation
MAX_RETRIES = 3
RETRY_DELAY = 2                          # Seconds between retries
OUTPUT_DIR = Path(__file__).parent / "output" / "writing_engine"

# ---------------------------------------------------------------------------
# Genre-specific system prompts
# ---------------------------------------------------------------------------
GENRE_PROMPTS = {
    "romance": {
        "system": (
            "You are a bestselling romance novelist. Write compelling, emotionally "
            "rich romance fiction with well-developed characters, romantic tension, "
            "and satisfying resolutions. Use vivid sensory details and authentic "
            "dialogue. Write in third-person limited POV. Each chapter should have "
            "a clear beginning, middle, and end with an emotional hook."
        ),
        "chapter_structure": (
            "Structure each chapter with:\n"
            "1. An evocative opening that sets mood and place\n"
            "2. Character interaction driving emotional connection\n"
            "3. Rising tension or conflict (internal or external)\n"
            "4. A turning point or revelation\n"
            "5. A chapter-ending hook that makes readers continue"
        ),
    },
    "business": {
        "system": (
            "You are an expert business writer and consultant. Write professional, "
            "persuasive business content including proposals, reports, pitch narratives, "
            "and strategy documents. Use clear structure, data-driven reasoning, and "
            "actionable insights. Write with authority while remaining accessible."
        ),
        "chapter_structure": (
            "Structure each section with:\n"
            "1. A clear header and executive summary of the section\n"
            "2. Supporting evidence, data points, or case studies\n"
            "3. Analysis and implications\n"
            "4. Actionable recommendations\n"
            "5. A transition to the next section"
        ),
    },
    "technical": {
        "system": (
            "You are a senior technical writer. Create clear, accurate, and well-"
            "organized technical documentation. Use precise language, code examples "
            "where appropriate, and maintain consistent terminology. Write for a "
            "competent audience that needs practical, implementable guidance."
        ),
        "chapter_structure": (
            "Structure each section with:\n"
            "1. A clear title and objective statement\n"
            "2. Prerequisites or context needed\n"
            "3. Step-by-step instructions or explanation\n"
            "4. Code examples, diagrams descriptions, or illustrations\n"
            "5. Common pitfalls and troubleshooting tips"
        ),
    },
    "blog": {
        "system": (
            "You are an engaging blog writer and content creator. Write conversational, "
            "valuable blog posts that inform and engage readers. Use a friendly tone, "
            "practical examples, and clear takeaways. Include hooks, subheadings, "
            "and calls to action where appropriate."
        ),
        "chapter_structure": (
            "Structure each section with:\n"
            "1. A catchy subheading\n"
            "2. A relatable hook or anecdote\n"
            "3. Core content with practical advice\n"
            "4. Real-world examples or case studies\n"
            "5. A clear takeaway or action item"
        ),
    },
    "fiction": {
        "system": (
            "You are a versatile fiction writer skilled across genres including "
            "thriller, sci-fi, fantasy, mystery, and literary fiction. Write vivid, "
            "immersive fiction with strong narrative voice, compelling characters, "
            "and well-paced plots. Use sensory details and authentic dialogue."
        ),
        "chapter_structure": (
            "Structure each chapter with:\n"
            "1. An atmospheric opening that grounds the reader\n"
            "2. Scene progression with clear goals and obstacles\n"
            "3. Character development through action and dialogue\n"
            "4. Tension escalation toward the chapter's climax\n"
            "5. A resolution or cliffhanger that propels the story forward"
        ),
    },
    "all": {
        "system": (
            "You are a versatile professional writer capable of producing high-quality "
            "content across multiple genres and formats. Match the tone, structure, "
            "and style to the content type specified. Maintain consistency throughout."
        ),
        "chapter_structure": (
            "Structure content logically with:\n"
            "1. Clear section headers and transitions\n"
            "2. Well-organized paragraphs with topic sentences\n"
            "3. Supporting details and examples\n"
            "4. Smooth flow between sections\n"
            "5. Strong section endings that connect to what follows"
        ),
    },
}

# ---------------------------------------------------------------------------
# Groq API wrapper
# ---------------------------------------------------------------------------
def init_groq_client():
    """Initialize Groq client with API key from env or config."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Try loading from local .env files
        candidates = [
            Path(__file__).parent.parent / ".env",      # project root
            Path.home() / "AppData/Local/hermes/.env",  # hermes config
        ]
        for env_file in candidates:
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY=") and not line.startswith("#"):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if api_key:
                break
    if not api_key:
        print("\n[ERROR] GROQ_API_KEY not found!")
        print("  Set it via:  export GROQ_API_KEY=gsk_xxxxxxxx")
        print("  Or add it to the .env file at the project root.")
        print("  Get a free key at: https://console.groq.com/keys")
        sys.exit(1)

    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception as e:
        print(f"[ERROR] Failed to initialize Groq client: {e}")
        sys.exit(1)


def generate_text(client, system_prompt: str, user_prompt: str,
                  temperature: float = 0.8, max_tokens: int = 4096) -> str:
    """Generate text using Groq API with retry and fallback logic."""
    models_to_try = [
        GROQ_MODEL,
        GROQ_THINKING_MODEL,
    ] if GROQ_THINKING_MODEL and GROQ_THINKING_MODEL != GROQ_MODEL else [GROQ_MODEL]

    for model in models_to_try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Build request kwargs
                kwargs = dict(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.9,
                )
                # Disable thinking for Qwen models to avoid token waste
                if "qwen" in model:
                    kwargs["extra_body"] = {"reasoning_effort": "none"}

                response = client.chat.completions.create(**kwargs)
                text = response.choices[0].message.content
                # Strip any remaining think blocks as safety
                if "<think>" in text or "<think>" in text:
                    import re
                    text = re.sub(r"<think>[\s\S]*?</think>", "", text)
                    text = re.sub(r"<think>[\s\S]*?</think>", "", text)
                    text = re.sub(r"<think>[\s\S]*", "", text)  # Unclosed think block
                    text = text.strip()
                return text

            except Exception as e:
                error_msg = str(e)
                if "not_found" in error_msg.lower() or "404" in error_msg:
                    print(f"\n  [FALLBACK] Model {model} unavailable, trying next...")
                    break  # Try next model, don't retry this one
                elif "rate_limit" in error_msg.lower() or "429" in error_msg:
                    wait = RETRY_DELAY * attempt * 2
                    print(f"\n  [RATE LIMIT] Waiting {wait}s before retry {attempt}/{MAX_RETRIES}...")
                    time.sleep(wait)
                else:
                    print(f"\n  [ERROR] Attempt {attempt}/{MAX_RETRIES}: {error_msg}")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
                    else:
                        # Try next model if available
                        break

    raise RuntimeError("All models failed. Check GROQ_API_KEY and network connection.")


# ---------------------------------------------------------------------------
# Content planning
# ---------------------------------------------------------------------------
def plan_content(client, genre: str, topic: str, target_words: int) -> dict:
    """Generate an outline/plan for the content."""
    genre_config = GENRE_PROMPTS.get(genre, GENRE_PROMPTS["all"])
    est_chapters = max(1, target_words // 1200)  # ~1200 words per chapter

    system = (
        f"{genre_config['system']}\n\n"
        f"{genre_config['chapter_structure']}\n\n"
        "You are now planning the content structure. Output ONLY valid JSON."
    )
    user = (
        f"Plan a {target_words}-word piece about: {topic}\n\n"
        f"Target: ~{est_chapters} chapters/sections.\n\n"
        "Return a JSON object with this exact structure:\n"
        '{\n'
        '  "title": "The title of the work",\n'
        '  "subtitle": "Optional subtitle or tagline",\n'
        '  "genre": "Detected genre description",\n'
        '  "tone": "Tone and style description",\n'
        '  "chapters": [\n'
        '    {"number": 1, "title": "Chapter Title", "summary": "Brief 1-2 sentence summary", "target_words": 800},\n'
        '    ...\n'
        '  ]\n'
        '}\n\n'
        "Output ONLY the JSON. No markdown fences, no commentary."
    )

    response = generate_text(client, system, user, temperature=0.4, max_tokens=2000)

    # Strip any remaining think blocks and markdown fences
    import re
    response = re.sub(r"<think>[\s\S]*?</think>", "", response)
    response = re.sub(r"<think>[\s\S]*?</think>", "", response)
    response = response.strip()

    # Parse JSON from response
    try:
        # Handle markdown code fences
        if "```" in response:
            match = re.search(r"```(?:json)?\s*\n?(.*?)```", response, re.DOTALL)
            if match:
                response = match.group(1)
        # Try to extract JSON object if there's surrounding text
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            response = json_match.group(0)
        return json.loads(response.strip())
    except json.JSONDecodeError:
        # Fallback: generate a basic outline
        print("  [WARN] Could not parse plan JSON, using fallback outline.")
        return generate_fallback_plan(genre, topic, target_words, est_chapters)


def generate_fallback_plan(genre: str, topic: str, target_words: int, chapters: int) -> dict:
    """Generate a fallback plan when JSON parsing fails."""
    words_per = target_words // chapters
    return {
        "title": topic[:100],
        "subtitle": "",
        "genre": genre,
        "tone": "Professional and engaging",
        "chapters": [
            {
                "number": i + 1,
                "title": f"Section {i + 1}",
                "summary": f"Part {i + 1} covering aspects of {topic}",
                "target_words": words_per,
            }
            for i in range(chapters)
        ],
    }


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------
def generate_chapter(client, genre: str, plan: dict, chapter_info: dict,
                     prev_summary: str = "", chapter_num: int = 1,
                     total_chapters: int = 1) -> str:
    """Generate a single chapter or section."""
    genre_config = GENRE_PROMPTS.get(genre, GENRE_PROMPTS["all"])

    system = (
        f"{genre_config['system']}\n\n"
        f"{genre_config['chapter_structure']}\n\n"
        "IMPORTANT RULES:\n"
        "- Write ONLY the chapter content. No meta-commentary.\n"
        "- Do NOT include chapter numbers or titles as headers — those are handled separately.\n"
        "- Write in a flowing, natural style.\n"
        "- Use complete sentences and well-formed paragraphs.\n"
        f"- Target approximately {chapter_info.get('target_words', 800)} words."
    )

    context_parts = [f"Title: {plan.get('title', 'Untitled')}"]
    if plan.get("subtitle"):
        context_parts.append(f"Subtitle: {plan['subtitle']}")
    context_parts.append(f"Genre: {plan.get('genre', genre)}")
    context_parts.append(f"Tone: {plan.get('tone', 'Professional')}")

    if prev_summary:
        context_parts.append(f"\nWhat happened before this chapter:\n{prev_summary}")

    context_parts.append(
        f"\nThis is chapter {chapter_num} of {total_chapters}.\n"
        f"Chapter title: {chapter_info['title']}\n"
        f"Chapter summary: {chapter_info['summary']}"
    )

    user = "\n".join(context_parts) + "\n\nWrite this chapter now:"
    # ~1.3 tokens per word, request 2x target to ensure we hit it
    target_tokens = min(4096, max(2048, chapter_info.get("target_words", 800) * 3))

    return generate_text(client, system, user, temperature=0.85, max_tokens=target_tokens)


def compile_full_content(plan: dict, chapters_text: list) -> str:
    """Assemble all chapters into a clean final document."""
    parts = []

    # Title page
    parts.append(plan.get("title", "Untitled").upper())
    if plan.get("subtitle"):
        parts.append(plan["subtitle"])
    parts.append(f"\nGenre: {plan.get('genre', 'General')}")
    parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    parts.append("=" * 60)
    parts.append("")

    # Table of contents
    parts.append("TABLE OF CONTENTS")
    parts.append("-" * 40)
    for ch in plan.get("chapters", []):
        parts.append(f"  {ch['number']}. {ch['title']}")
    parts.append("")
    parts.append("=" * 60)
    parts.append("")

    # Chapters
    for ch_plan, ch_text in zip(plan.get("chapters", []), chapters_text):
        parts.append("")
        header = f"Chapter {ch_plan['number']}: {ch_plan['title']}"
        parts.append(header)
        parts.append("-" * len(header))
        parts.append("")
        parts.append(ch_text.strip())
        parts.append("")

    # Footer
    parts.append("")
    parts.append("=" * 60)
    parts.append("END OF DOCUMENT")
    total_words = sum(len(t.split()) for t in chapters_text)
    parts.append(f"Total word count: {total_words:,}")
    parts.append(f"Chapters: {len(chapters_text)}")
    parts.append("Generated by GoGetter Writing Engine v1.0")
    parts.append("=" * 60)

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run_writing_engine(genre: str, topic: str, target_words: int,
                       output_name: str = None, keep_json: bool = False):
    """Main writing pipeline."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  GoGetter Writing Engine v1.0")
    print("=" * 60)
    print(f"  Genre:      {genre}")
    print(f"  Topic:      {topic}")
    print(f"  Target:     {target_words:,} words")
    print(f"  Model:      {GROQ_MODEL}")
    print(f"  Output dir: {OUTPUT_DIR}")
    print("=" * 60 + "\n")

    # Initialize
    client = init_groq_client()
    start_time = time.time()

    # Step 1: Plan
    print("[1/3] Planning content structure...")
    plan = plan_content(client, genre, topic, target_words)
    chapters = plan.get("chapters", [])

    if not chapters:
        print("[ERROR] Plan returned no chapters. Aborting.")
        return None

    print(f"  ✓ Title: {plan.get('title', 'Untitled')}")
    print(f"  ✓ Chapters planned: {len(chapters)}")
    for ch in chapters:
        print(f"    - Ch.{ch['number']}: {ch['title']} (~{ch.get('target_words', 800)} words)")

    # Save plan JSON for reference
    if keep_json:
        plan_file = OUTPUT_DIR / f"{_safe_filename(plan.get('title', topic))}_plan.json"
        plan_file.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
        print(f"  ✓ Plan saved: {plan_file}")

    # Step 2: Generate
    print(f"\n[2/3] Generating content ({len(chapters)} chapters)...")
    chapters_text = []
    total_words = 0
    prev_summary = ""

    for i, ch in enumerate(chapters):
        ch_start = time.time()
        print(f"\n  [{i+1}/{len(chapters)}] Writing: {ch['title']}...", end=" ", flush=True)

        text = generate_chapter(
            client, genre, plan, ch,
            prev_summary=prev_summary,
            chapter_num=ch["number"],
            total_chapters=len(chapters),
        )

        if not text:
            print("FAILED (empty response)")
            text = f"[Chapter content generation failed. Topic: {ch['summary']}]"

        chapters_text.append(text)
        ch_words = len(text.split())
        total_words += ch_words
        ch_time = time.time() - ch_start
        print(f"✓ {ch_words:,} words ({ch_time:.1f}s)")

        # Brief summary of this chapter for continuity
        if i < len(chapters) - 1:
            prev_summary = f"Chapter {ch['number']} ('{ch['title']}') covered: {ch['summary']}"
        progress = ((i + 1) / len(chapters)) * 100
        print(f"  Progress: {progress:.0f}% | Total words so far: {total_words:,}")

    # Step 3: Compile
    print(f"\n[3/3] Compiling final document...")
    final_text = compile_full_content(plan, chapters_text)

    # Determine output filename
    if not output_name:
        output_name = _safe_filename(plan.get("title", topic))

    output_file = OUTPUT_DIR / f"{output_name}.txt"
    output_file.write_text(final_text, encoding="utf-8")

    elapsed = time.time() - start_time
    final_words = len(final_text.split())

    print(f"\n{'=' * 60}")
    print(f"  COMPLETE!")
    print(f"{'=' * 60}")
    print(f"  File:      {output_file}")
    print(f"  Words:     {final_words:,}")
    print(f"  Chapters:  {len(chapters)}")
    print(f"  Time:      {elapsed:.1f}s")
    print(f"  Speed:     {final_words / max(1, elapsed):.0f} words/sec")
    print(f"{'=' * 60}\n")

    return str(output_file)


def _safe_filename(name: str) -> str:
    """Convert a string to a safe filename."""
    import re
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:80] or "writing_output"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="GoGetter Writing Engine — AI-powered content generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s --genre romance --topic "Second-chance love in Tuscany" --words 5000
              %(prog)s --genre business --topic "Series A pitch narrative" --words 2500
              %(prog)s --genre technical --topic "React authentication guide" --words 3000
              %(prog)s --genre blog --topic "10 SEO tips for 2025" --words 1500
              %(prog)s --genre fiction --topic "Space station thriller" --words 8000
        """),
    )
    parser.add_argument("--genre", "-g",
                        choices=list(GENRE_PROMPTS.keys()),
                        help="Genre of content to generate")
    parser.add_argument("--topic", "-t",
                        help="Topic, premise, or description of what to write")
    parser.add_argument("--words", "-w", type=int, default=3000,
                        help="Target word count (default: 3000)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output filename (without extension)")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Also save the plan as a JSON file")
    parser.add_argument("--list-genres", action="store_true",
                        help="List available genres and exit")

    args = parser.parse_args()

    if args.list_genres:
        print("\nAvailable genres:")
        for name, config in GENRE_PROMPTS.items():
            print(f"  {name:12s} — {config['system'][:70]}...")
        print()
        sys.exit(0)

    if not args.genre or not args.topic:
        parser.error("--genre and --topic are required (use --list-genres to see options)")

    if args.words < 500:
        print("[ERROR] Minimum word count is 500. Use --words 500 or higher.")
        sys.exit(1)

    result = run_writing_engine(
        genre=args.genre,
        topic=args.topic,
        target_words=args.words,
        output_name=args.output,
        keep_json=args.json,
    )

    if result:
        print(f"\nDone! Your content is ready at:\n  {result}")
    else:
        print("\n[ERROR] Writing engine failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
