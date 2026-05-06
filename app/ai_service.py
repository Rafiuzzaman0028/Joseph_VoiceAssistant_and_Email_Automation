import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_system_prompt():
    with open("app/prompt.txt", "r") as f:
        return f.read()

def generate_ai_reply(context: dict):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": get_system_prompt(),
            },
            {
                "role": "user",
                "content": f"""
Backend context and message:
{json.dumps(context, indent=2)}

Task:
Write one customer reply based on the rules and context above.
""",
            },
        ],
    )

    return response.choices[0].message.content
