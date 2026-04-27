"""
RAG Chat Module for PDF-based responses.
Generates answers based on retrieved manual content and appends exact references.
"""
import os
from typing import List

from dotenv import load_dotenv

from pdf_retriever import retrieve_similar_chunks
from vector_store_utils import get_openai_client

load_dotenv()


def create_system_prompt(context_text: str, has_context: bool = True):
    """Create the system prompt for the PDF-based support assistant."""
    base_prompt = (
        "You are the Bavis Support Assistant.\n\n"
        "You help users with assembly, installation, setup, operation, troubleshooting, "
        "product specifications, compatibility, maintenance, and service guidance for Bavis products.\n\n"
        "Rules:\n"
        "1. For greetings or casual conversation, respond naturally and briefly.\n"
        "2. For technical or product-support questions, use only the provided manual excerpts.\n"
        "3. Do not invent procedures, measurements, compatibility notes, or safety instructions.\n"
        "4. If the manuals do not contain the requested information, say that you could not locate it in the loaded manuals.\n"
        "5. Keep technical answers practical and easy to follow.\n"
        "6. For follow-up questions in the same conversation, assume the user is still asking about the same product or procedure unless they clearly switch topics.\n"
        "7. When steps exist in the excerpts, present them in the order shown.\n"
        "8. Do not include references, PDF names, or page numbers unless the user explicitly asks for them.\n"
        "9. If the user asks where to find the information, which manual it came from, which PDF to open, or which page to check, then provide those details clearly.\n"
    )

    if has_context and context_text:
        base_prompt += (
            f"\nManual excerpts:\n{context_text}\n\n"
            "Answer the user's question directly from these excerpts."
        )
    else:
        base_prompt += (
            "\nNo manual excerpts were retrieved for this question. "
            "If the user is asking a technical question, explain that the needed detail was not located."
        )

    return {"role": "system", "content": base_prompt}


def expand_query_for_retrieval(query: str):
    """Expand support queries with a few related terms to improve recall."""
    query_lower = query.lower()

    if "security" in query_lower:
        return f"{query} bullet-resistant secure protection transaction window drawer"
    if "install" in query_lower or "assembly" in query_lower or "assemble" in query_lower:
        return f"{query} installation setup assembly mounting wiring instructions"
    if "service" in query_lower or "repair" in query_lower or "troubleshoot" in query_lower:
        return f"{query} service troubleshooting maintenance adjustment problem issue"
    if "manual" in query_lower or "guide" in query_lower or "page" in query_lower:
        return f"{query} user manual service manual installation guide page reference"
    return query


def find_previous_substantive_user_query(history: list) -> str:
    """Find the most recent user query that likely contains the product/procedure context."""
    skip_terms = {
        "hi",
        "hello",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "page?",
        "reference?",
        "source?",
    }

    for item in reversed(history):
        if item.get("role") != "user":
            continue
        content = (item.get("content") or "").strip()
        if not content:
            continue
        if content.lower() in skip_terms:
            continue
        if user_requested_references(content):
            continue
        return content

    return ""


def is_context_dependent_followup(user_query: str, history: list) -> bool:
    """Detect short follow-up questions that rely on the previous topic."""
    if not history:
        return False

    query_lower = user_query.lower().strip()
    words = query_lower.split()
    followup_signals = [
        "this",
        "that",
        "it",
        "they",
        "them",
        "these",
        "those",
        "caution",
        "warning",
        "step",
        "next",
        "after",
        "before",
        "where",
        "which",
        "page",
        "reference",
        "source",
    ]

    if len(words) <= 12 and any(signal in query_lower for signal in followup_signals):
        return True

    return False


def build_retrieval_query(user_query: str, history: list) -> str:
    """Blend the current question with previous context when the user asks a dependent follow-up."""
    if is_reference_only_request(user_query):
        previous_query = find_previous_substantive_user_query(history)
        previous_answer = find_previous_assistant_answer(history)
        parts = [part for part in [previous_query, previous_answer, user_query] if part]
        if parts:
            return "\n".join(parts)
        return user_query

    if not is_context_dependent_followup(user_query, history):
        return user_query

    previous_query = find_previous_substantive_user_query(history)
    if not previous_query or previous_query.strip().lower() == user_query.strip().lower():
        return user_query

    return f"{previous_query}\nFollow-up question: {user_query}"


def build_context_text(chunks: List[dict]) -> str:
    context_parts = []
    for chunk in chunks:
        source_info = f"[PDF: {chunk.get('source', 'Unknown')}, Page: {chunk.get('page', 'N/A')}]"
        context_parts.append(f"{source_info}\n{chunk['text']}")
    return "\n\n---\n\n".join(context_parts)


def build_reference_block(chunks: List[dict]) -> str:
    seen = set()
    lines = []

    for chunk in chunks:
        source = chunk.get("source") or "Unknown PDF"
        page = chunk.get("page")
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        if page:
            lines.append(f"- {source}, page {page}")
        else:
            lines.append(f"- {source}")
        if len(lines) == 4:
            break

    if not lines:
        return ""

    return "\n\nReferences:\n" + "\n".join(lines)


def user_requested_references(user_query: str) -> bool:
    """Return True when the user explicitly asks for source details."""
    query_lower = user_query.lower()
    reference_signals = [
        "reference",
        "references",
        "source",
        "sources",
        "manual",
        "pdf",
        "page",
        "where to find",
        "where can i find",
        "where do i find",
        "where is this in",
        "which guide",
        "which manual",
        "which pdf",
        "show me the page",
        "give me the page",
    ]
    return any(signal in query_lower for signal in reference_signals)


def is_reference_only_request(user_query: str) -> bool:
    """Detect short follow-up questions that only ask for source/page details."""
    query_lower = user_query.lower().strip()
    reference_only_phrases = [
        "where to find",
        "where can i find",
        "where do i find",
        "where did you get",
        "which page",
        "what page",
        "page?",
        "source?",
        "reference?",
        "which manual",
        "which pdf",
    ]
    if len(query_lower.split()) <= 6 and user_requested_references(query_lower):
        return True
    return any(phrase in query_lower for phrase in reference_only_phrases)


def find_previous_assistant_answer(history: list) -> str:
    """Return the most recent assistant answer to anchor a reference-only follow-up."""
    for item in reversed(history):
        if item.get("role") == "assistant":
            return (item.get("content") or "").strip()
    return ""


def collect_reference_matches(chunks: List[dict], max_matches: int = 2) -> List[dict]:
    """Return the strongest unique matches, usually just one reference."""
    matches = []
    seen = set()

    for chunk in chunks:
        source = chunk.get("source") or "Unknown PDF"
        page = chunk.get("page")
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        matches.append(
            {
                "source": source,
                "page": page,
                "similarity": float(chunk.get("similarity", 0)),
            }
        )
        if len(matches) == max_matches:
            break

    if len(matches) <= 1:
        return matches

    if matches[0]["similarity"] - matches[1]["similarity"] > 0.02:
        return [matches[0]]

    return matches


def build_reference_response(user_query: str, chunks: List[dict]) -> str:
    """Build a concise reference-only response from the strongest page match."""
    matches = collect_reference_matches(chunks, max_matches=2)
    if not matches:
        return "I could not identify the exact manual page for that answer."

    if len(matches) == 1:
        match = matches[0]
        if match["page"]:
            if "page" in user_query.lower():
                return f"This is on page {match['page']} of {match['source']}."
            return f"This info is in {match['source']}, page {match['page']}."
        return f"This info is in {match['source']}."

    lines = []
    for match in matches:
        if match["page"]:
            lines.append(f"- {match['source']}, page {match['page']}")
        else:
            lines.append(f"- {match['source']}")
    return "The closest matching references are:\n" + "\n".join(lines)


def generate_answer(user_query: str, history: list):
    """
    Generate an answer using chat history and manual-backed RAG.
    """
    normalized_query = user_query.strip()
    retrieval_query = build_retrieval_query(normalized_query, history)
    expanded_query = expand_query_for_retrieval(retrieval_query)

    retrieved_chunks = retrieve_similar_chunks(expanded_query, top_k=8)
    filtered_chunks = [chunk for chunk in retrieved_chunks if chunk.get("similarity", 0) >= 0.3]

    if is_reference_only_request(normalized_query):
        return build_reference_response(normalized_query, filtered_chunks)

    has_context = bool(filtered_chunks)
    context_text = build_context_text(filtered_chunks) if has_context else ""

    chat_history = [{"role": item["role"], "content": item["content"]} for item in history]
    system_prompt = create_system_prompt(context_text, has_context=has_context)
    messages = [system_prompt] + chat_history + [{"role": "user", "content": user_query}]

    try:
        response = get_openai_client().chat.completions.create(
            model=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.2,
            seed=42,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as exc:
        return f"Error generating a response: {exc}"

    if has_context and user_requested_references(user_query):
        answer += build_reference_block(filtered_chunks)

    return answer
