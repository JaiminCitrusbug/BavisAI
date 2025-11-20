"""
RAG Chat Module for PDF-based Responses
Generates answers strictly based on retrieved PDF content from vector database.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from pdf_retriever import retrieve_similar_chunks

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def create_system_prompt(context_text: str):
    """
    Create the system prompt for the PDF-based RAG assistant.
    Responses must be strictly based on the retrieved context.
    """
    return {
        "role": "system",
        "content": (
            "You are a professional Drive-Thru Lane Advisor assistant that helps users find information "
            "about drive-thru and teller-lane systems based on product documentation and datasheets.\n\n"
            
            "CRITICAL RULES:\n"
            "1. You MUST answer questions STRICTLY based on the provided context from the knowledge base.\n"
            "2. If the context does not contain relevant information to answer the question, "
            "you must clearly state: 'I don't have that information in my knowledge base. "
            "Could you please rephrase your question or ask about something else?'\n"
            "3. NEVER invent, guess, or fabricate information. Only use what is explicitly provided in the context.\n"
            "4. If multiple relevant pieces of information are found, synthesize them clearly.\n"
            "5. When providing technical specifications, measurements, or product details, "
            "cite them exactly as they appear in the context.\n"
            "6. Be concise, professional, and helpful.\n"
            "7. If asked about products, systems, or features not mentioned in the context, "
            "clearly state that this information is not available.\n\n"
            
            "Response Style:\n"
            "- Be direct and factual\n"
            "- Use clear, professional language\n"
            "- When possible, mention the source document or page number if available\n"
            "- Structure your response logically\n"
            "- If providing specifications, list them clearly\n\n"
            
            f"Context from knowledge base:\n{context_text}\n\n"
            
            "Remember: Your answers must be based ONLY on the context provided above. "
            "If the context doesn't contain the answer, say so clearly."
        ),
    }


def generate_answer(user_query: str, history: list):
    """
    Generate context-aware answer using chat history and RAG from PDF vector database.
    Ensures consistent responses by using deterministic retrieval and generation.
    
    Args:
        user_query: Current user query
        history: Conversation history (list of message dicts with 'role' and 'content')
        
    Returns:
        Generated answer string
    """
    # Normalize query for consistent retrieval (handled in retriever, but ensure consistency here too)
    normalized_query = user_query.strip()
    
    # Retrieve relevant chunks from vector database (chunks are sorted deterministically)
    retrieved_chunks = retrieve_similar_chunks(normalized_query, top_k=5)
    
    if not retrieved_chunks:
        return (
            "I couldn't find any relevant information in my knowledge base for your query. "
            "Please try rephrasing your question or ask about drive-thru systems, product specifications, "
            "or installation requirements."
        )
    
    # Build context text from retrieved chunks in deterministic order
    # Chunks are already sorted by similarity, source, page, and chunk_index in retriever
    context_parts = []
    for chunk in retrieved_chunks:
        source_info = f"[Source: {chunk.get('source', 'Unknown')}, Page: {chunk.get('page', 'N/A')}]"
        context_parts.append(f"{source_info}\n{chunk['text']}")
    
    # Join with consistent separator for deterministic context
    context_text = "\n\n---\n\n".join(context_parts)
    
    # Convert Streamlit history to OpenAI chat format
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history]
    system_prompt = create_system_prompt(context_text)
    
    # Build messages: system prompt + history + current query
    messages = [system_prompt] + chat_history + [{"role": "user", "content": user_query}]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0,  # Zero temperature for maximum consistency and deterministic responses
            seed=42,  # Fixed seed for reproducibility
        )
        
        answer = response.choices[0].message.content.strip()
        return answer
        
    except Exception as e:
        return f"⚠️ There was an error generating a response: {str(e)}"

