import os
from groq import Groq
from app.core.config import settings

# Assume settings has GROQ_API_KEY and GROQ_MODEL (default "llama3-70b-8192" or "mixtral-8x7b-32768")
client = Groq(api_key=settings.GROQ_API_KEY)

async def call_groq(prompt: str, system_prompt: str = None, max_tokens: int = 500) -> dict:
    """Call GroqCloud LLM and return response text and token usage."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL or "llama3-70b-8192",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return {
        "text": completion.choices[0].message.content,
        "model": settings.GROQ_MODEL or "llama3-70b-8192",
        "tokens": completion.usage.total_tokens if completion.usage else None
    }