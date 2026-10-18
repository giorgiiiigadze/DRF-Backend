import os
from openai import OpenAI


class SummarizerError(Exception):
    """A user-safe failure raised when a summary cannot be generated."""


class Summarizer:
    """Summary provider boundary; replace this implementation for a local model later."""

    def summarize(self, transcript, style):
        api_key = os.environ.get("OPENAI_API_KEY")
        model = os.environ.get("OPENAI_MODEL")
        if not api_key:
            raise SummarizerError("Summary service is not configured: OPENAI_API_KEY is missing.")
        if not model:
            raise SummarizerError("Summary service is not configured: OPENAI_MODEL is missing.")
        if not transcript.strip():
            raise SummarizerError("Cannot summarize a session with no transcript segments.")

        try:
            response = OpenAI(api_key=api_key).chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"Summarize the supplied live-caption transcript in a {style} style. Do not invent details."},
                    {"role": "user", "content": transcript},
                ],
            )
            text = response.choices[0].message.content
            if not text:
                raise SummarizerError("The summary service returned an empty response.")
            return text.strip()
        except SummarizerError:
            raise
        except Exception as exc:
            raise SummarizerError("The summary service is unavailable. Please try again later.") from exc
