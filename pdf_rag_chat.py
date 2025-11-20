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


def create_system_prompt(context_text: str, has_context: bool = True):
    """
    Create the system prompt for the PDF-based RAG assistant.
    Handles both RAG-based queries and conversational interactions.
    """
    base_prompt = (
        "You are a professional Drive-Thru Lane Advisor assistant that helps users find information "
        "about drive-thru and teller-lane systems based on product documentation and datasheets.\n\n"
        
        "RESPONSE GUIDELINES:\n"
        "1. For greetings, casual conversation, or general questions: Respond naturally and helpfully. "
        "You can engage in friendly conversation and guide users toward asking about drive-thru systems.\n"
        "2. For technical questions about products, systems, or specifications: Use ONLY the provided context "
        "from the knowledge base. Never invent or fabricate technical information.\n"
        "3. If the context contains relevant information, synthesize it clearly and provide a helpful answer.\n"
        "4. If the context doesn't contain relevant information for a technical question, politely explain "
        "that you don't have that specific information and suggest rephrasing or asking about related topics.\n"
        "5. When providing technical specifications, measurements, or product details, "
        "cite them exactly as they appear in the context.\n"
        "6. Be professional, helpful, and conversational.\n\n"
        
        "CRITICAL RESPONSE STYLE RULES:\n"
        "- NEVER use phrases like 'Based on the information available', 'Based on the data', "
        "'Based on my knowledge base', 'According to the documentation', or similar qualifiers\n"
        "- Provide answers directly and naturally, as if you know the information firsthand\n"
        "- Do not mention the retrieval process, knowledge base, or data sources in your responses\n"
        "- Be natural and conversational for greetings and casual interactions\n"
        "- Be direct and factual for technical questions\n"
        "- Use clear, professional language\n"
        "- Structure technical responses logically\n"
        "- If providing specifications, list them clearly\n"
        "- Simply present the information as facts, without referencing where it came from\n\n"
    )
    
    if has_context and context_text:
        base_prompt += (
            f"Context from knowledge base:\n{context_text}\n\n"
            "For technical questions, use the context above to provide direct answers. "
            "Present the information naturally without mentioning sources, data, or knowledge base. "
            "For greetings or general conversation, respond naturally without requiring context."
        )
    else:
        base_prompt += (
            "No specific context was retrieved for this query. "
            "If this is a greeting or general question, respond naturally. "
            "If this is a technical question, politely explain that you need more specific information."
        )
    
    return {
        "role": "system",
        "content": base_prompt,
    }


def expand_query_for_retrieval(query: str):
    """
    Expand query with related terms to improve retrieval, especially for semantic concepts.
    """
    query_lower = query.lower()
    
    # Security-related expansions
    if "security" in query_lower:
        return f"{query} bullet-resistant secure protection safety window drawer"
    
    # Solution/product-related expansions
    if "solution" in query_lower and "security" in query_lower:
        return f"{query} window drawer combination bullet-resistant glass secure transaction"
    
    # Restaurant/food-related expansions
    if "restaurant" in query_lower or "food" in query_lower:
        return f"{query} drive-thru food service quick service"
    
    # Return original query if no expansion needed
    return query


def generate_answer(user_query: str, history: list):
    """
    Generate context-aware answer using chat history and RAG from PDF vector database.
    Handles both technical queries (using RAG) and conversational queries (natural responses).
    
    Args:
        user_query: Current user query
        history: Conversation history (list of message dicts with 'role' and 'content')
        
    Returns:
        Generated answer string
    """
    # Normalize query for consistent retrieval
    normalized_query = user_query.strip()
    
    # Expand query for better retrieval, especially for semantic concepts
    expanded_query = expand_query_for_retrieval(normalized_query)
    
    # Retrieve relevant chunks from vector database with increased top_k for better coverage
    # Using top_k=8 to get more context, especially for broader queries like "security"
    retrieved_chunks = retrieve_similar_chunks(expanded_query, top_k=8)
    
    # Filter chunks by similarity threshold to ensure quality
    # Lower threshold (0.3) to catch more relevant content, especially for semantic matches
    filtered_chunks = [chunk for chunk in retrieved_chunks if chunk.get("similarity", 0) >= 0.3]
    
    # Build context text from retrieved chunks in deterministic order
    context_text = ""
    has_context = False
    
    if filtered_chunks:
        context_parts = []
        for chunk in filtered_chunks:
            source_info = f"[Source: {chunk.get('source', 'Unknown')}, Page: {chunk.get('page', 'N/A')}]"
            context_parts.append(f"{source_info}\n{chunk['text']}")
        
        # Join with consistent separator for deterministic context
        context_text = "\n\n---\n\n".join(context_parts)
        has_context = True
    
    # Convert Streamlit history to OpenAI chat format
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history]
    system_prompt = create_system_prompt(context_text, has_context=has_context)
    
    # Build messages: system prompt + history + current query
    messages = [system_prompt] + chat_history + [{"role": "user", "content": user_query}]
    
    try:
        # Use slightly higher temperature for more natural conversational responses
        # while still maintaining consistency for technical answers
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,  # Slightly higher for natural conversation, but still consistent
            seed=42,  # Fixed seed for reproducibility
        )
        
        answer = response.choices[0].message.content.strip()
        return answer
        
    except Exception as e:
        return f"⚠️ There was an error generating a response: {str(e)}"

