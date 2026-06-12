"""
Content Generation Service
---------------------------
Uses Groq (Llama 3.3) to generate structured, exam-ready study guides.
Fast, free, no billing needed.
"""

import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)


# ── Prompt Builder ────────────────────────────────────────────────

def build_prompt(
    note_text: str,
    chapter_title: str,
    chapter_description: str = "",
    subject: str = "",
) -> str:
    subject_line = f"Subject: {subject}\n" if subject else ""

    return f"""You are an expert study guide creator for university students preparing for exams.

{subject_line}Syllabus Chapter: {chapter_title}
Chapter Description: {chapter_description}

Student's Raw Notes:
{note_text}

---

Generate a structured study guide in this exact Markdown format:

# {chapter_title}

## Key Concepts
- List the main concepts as clear bullet points

## Detailed Notes
Clean organized explanation of all topics. Use sub-headings where needed.

## Important Definitions
| Term | Definition |
|------|------------|
| term | definition |

## Exam Tips
- List 3-5 things most likely to appear in exams

## Practice Questions
1. First likely exam question
2. Second likely exam question
3. Third likely exam question

Fix any OCR errors in the notes. Keep language simple and exam-focused."""


# ── Groq Generation ───────────────────────────────────────────────

def generate_study_guide(
    note_text: str,
    chapter_title: str,
    chapter_description: str = "",
    subject: str = "",
) -> dict:
    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key:
        return {
            "success": False,
            "content": "",
            "model": "",
            "message": "GROQ_API_KEY not set in environment",
        }

    try:
        client = Groq(api_key=api_key)

        prompt = build_prompt(
            note_text=note_text,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            subject=subject,
        )

        logger.info(f"Generating study guide for: {chapter_title}")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert study guide creator. Always respond in clean Markdown format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2048,
        )

        content = response.choices[0].message.content
        logger.info(f"Generated {len(content)} characters")

        return {
            "success": True,
            "content": content,
            "model":   "llama-3.3-70b-versatile",
            "message": "Study guide generated successfully",
        }

    except Exception as e:
        logger.error(f"Groq generation failed: {e}")
        return {
            "success": False,
            "content": "",
            "model":   "llama-3.3-70b-versatile",
            "message": str(e),
        }


# ── Streaming Version ─────────────────────────────────────────────

async def generate_study_guide_stream(
    note_text: str,
    chapter_title: str,
    chapter_description: str = "",
    subject: str = "",
):
    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key:
        yield "Error: GROQ_API_KEY not configured"
        return

    try:
        client = Groq(api_key=api_key)

        prompt = build_prompt(
            note_text=note_text,
            chapter_title=chapter_title,
            chapter_description=chapter_description,
            subject=subject,
        )

        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert study guide creator. Always respond in clean Markdown format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2048,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    except Exception as e:
        logger.error(f"Streaming generation failed: {e}")
        yield f"Error: {str(e)}"