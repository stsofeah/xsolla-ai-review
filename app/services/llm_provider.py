import os

def review_diff_llm(diff: str, max_findings: int):
    """
    Placeholder implementation for the LLM provider.

    Reads the API key from the OPENAI_API_KEY environment variable.
    Raises a RuntimeError when the provider is not configured or unavailable.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("LLM provider is not configured.")

    raise RuntimeError("LLM provider is unavailable.")