import os
from dotenv import load_dotenv
from openai import OpenAI
from langsmith.wrappers import wrap_openai

load_dotenv()



client = wrap_openai(
    OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
)

MODEL = os.getenv("MODEL")

MAX_CALLS = 20
calls_made = 0


def ask(system_prompt, user_message):
    """Send one request to the model and return its text reply."""
    global calls_made
    if calls_made >= MAX_CALLS:
        raise RuntimeError("Call budget reached. Stopping to protect the free limit.")
    calls_made += 1

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content