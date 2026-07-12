import httpx

from app.search import SearchResult, search_code

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder"
GENERATION_TIMEOUT_SECONDS = 120

PROMPT_TEMPLATE = """You are a code assistant answering questions about a repository.

Answer the question using ONLY the code context below. Every claim in your answer
must cite the file and function/class it comes from, in the form (file_path :: name).
If the context does not contain enough information to answer the question, say so
plainly instead of guessing.

Context:
{context}

Question: {question}

Answer:"""


class OllamaError(Exception):
    """Raised when the local LLM cannot be reached or fails to generate."""


def format_chunk(chunk: SearchResult) -> str:
    return f"--- {chunk.file_path} :: {chunk.name} ({chunk.kind}) ---\n{chunk.source}"


def build_prompt(question: str, chunks: list[SearchResult]) -> str:
    context = "\n\n".join(format_chunk(chunk) for chunk in chunks)
    return PROMPT_TEMPLATE.format(context=context, question=question)


def generate_answer(prompt: str) -> str:
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=GENERATION_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Local LLM request failed: {exc}") from exc

    answer = response.json().get("response")
    if not answer:
        raise OllamaError("Local LLM returned an empty response")
    return answer.strip()


def answer_question(repo: str, question: str, limit: int = 5) -> dict:
    chunks = search_code(repo, question, limit)
    if not chunks:
        return {
            "answer": "No indexed code was found for this repository, so the question cannot be answered.",
            "sources": [],
            "repo": repo,
        }

    prompt = build_prompt(question, chunks)
    answer = generate_answer(prompt)
    return {"answer": answer, "sources": chunks, "repo": repo}
