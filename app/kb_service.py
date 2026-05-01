import os
import pickle
import numpy as np
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

KB_FOLDER = "app/knowledge_base"
INDEX_FILE = "app/kb_index.pkl"
EMBEDDING_MODEL = "text-embedding-3-small"


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def embed_text(text: str):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def build_kb_index():
    documents = []

    for filename in os.listdir(KB_FOLDER):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(KB_FOLDER, filename)
            text = extract_text_from_pdf(path)
            chunks = chunk_text(text)

            for chunk in chunks:
                documents.append({
                    "source": filename,
                    "text": chunk,
                    "embedding": embed_text(chunk),
                })

    with open(INDEX_FILE, "wb") as f:
        pickle.dump(documents, f)

    return len(documents)


def load_kb_index():
    if not os.path.exists(INDEX_FILE):
        build_kb_index()

    with open(INDEX_FILE, "rb") as f:
        return pickle.load(f)


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def search_knowledge_base(question: str, top_k: int = 4):
    documents = load_kb_index()
    question_embedding = embed_text(question)

    scored_docs = []

    for doc in documents:
        score = cosine_similarity(question_embedding, doc["embedding"])

        scored_docs.append({
            "score": score,
            "source": doc["source"],
            "text": doc["text"],
        })

    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    return scored_docs[:top_k]