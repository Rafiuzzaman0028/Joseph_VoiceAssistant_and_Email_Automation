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

def generate_faq_answer(question: str, kb_context: list):
    context_text = "\n\n".join([doc['text'] for doc in kb_context])
    
    system_prompt = """You are Spartacus Bubble Soccer's professional UK voice assistant.
Your task is to answer the user's FAQ question using ONLY the provided knowledge base context.

RULES:
1. Keep your answer brief, conversational, and natural for speech (1-3 sentences maximum).
2. Never invent or hallucinate information. If the answer is not fully contained in the context, say "I'm sorry, I don't have that exact detail right now. Our team can confirm it for you by email."
3. Verbalize numbers and currency clearly (e.g., say "forty-nine pounds" instead of "£49", "fourteen" instead of "14").
4. If asked about payments, ensure you mention both the deposit amount AND when the balance is due if the context contains it.
5. Do not use markdown formatting (no asterisks, bolding, etc) as this is for text-to-speech.
6. Use your intelligence to answer using related concepts if asked (e.g., if asked about "restrooms", use context about "changing rooms").
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Knowledge Base Context:\n{context_text}\n\nQuestion: {question}"}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content.strip()
