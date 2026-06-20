import os
import json
import re
import google.generativeai as genai
import chromadb
from ingest import GeminiEmbeddingFunction

def get_chroma_collection(api_key, persist_dir="chroma_db"):
    """Get the active persistent ChromaDB collection."""
    try:
        client = chromadb.PersistentClient(path=persist_dir)
        embedding_fn = GeminiEmbeddingFunction(api_key)
        # Attempt to retrieve collection
        collection = client.get_collection(name="support_kb", embedding_function=embedding_fn)
        return collection
    except Exception as e:
        print(f"Error accessing Chroma DB collection: {e}")
        return None

def classify_persona(api_key, query, history=[]):
    """Classify user query using Gemini API and structured instructions."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Compile conversation context
    history_context = ""
    if history:
        history_context = "Conversation history:\n"
        for turn in history[-3:]: # Look at last 3 turns
            history_context += f"User: {turn['query']}\nAgent: {turn['response'][:100]}...\n"
            
    prompt = f"""You are an expert user behavior analyst. Analyze the incoming user message and classify the user's persona and sentiment traits.

Incoming message: "{query}"
{history_context}

Follow these classification rules:
1. PRIMARY PERSONA (choose exactly one):
- "Technical Expert": Uses technical terms (APIs, logs, port, timeout, code, JSON), expects detailed diagnostics or parameters.
- "Frustrated User": Employs emotional language, exclamation marks, urgency phrases ("now", "immediately", "broken", "wasted hours"), complains.
- "Business Executive": Focuses on ROI, SLA, timelines, cost, business uptime, brevity.

2. SECONDARY ATTRIBUTES:
- Sentiment: Integer between -5 (very negative) and +5 (very positive).
- Emotion: "frustrated", "anxious", "angry", "confused", "neutral", "satisfied", "pleased".
- Urgency: "low", "medium", "high", "critical".
- Complexity: "simple", "moderate", "complex", "enterprise-critical".
- Language: Detect the language of the query (e.g. "English", "Spanish", "Hindi", etc.).

Output your classification in EXACTLY the following JSON format. Do not include markdown code block syntax (like ```json).
{{
  "primaryPersona": "Technical Expert" | "Frustrated User" | "Business Executive",
  "sentiment": 0,
  "emotion": "neutral",
  "urgency": "medium",
  "complexity": "moderate",
  "language": "English"
}}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean any markdown code blocks from LLM output
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        classification = json.loads(text)
        return classification
    except Exception as e:
        print(f"LLM Classification failed: {e}. Falling back to rules.")
        # Fallback basic rule-based classifier
        return run_rule_based_classification_fallback(query)

def run_rule_based_classification_fallback(query):
    q = query.lower()
    persona = "Technical Expert"
    sentiment = 0
    emotion = "neutral"
    urgency = "medium"
    complexity = "moderate"
    
    if any(x in q for x in ["broken", "useless", "terrible", "worst", "waste", "urgent", "now", "immediately", "!!!"]):
        persona = "Frustrated User"
        sentiment = -3
        emotion = "frustrated"
        urgency = "high"
    elif any(x in q for x in ["sla", "roi", "uptime", "timeline", "cost", "impact", "business", "billing"]):
        persona = "Business Executive"
        emotion = "neutral"
        complexity = "enterprise-critical"
    
    return {
        "primaryPersona": persona,
        "sentiment": sentiment,
        "emotion": emotion,
        "urgency": urgency,
        "complexity": complexity,
        "language": "English"
    }

def retrieve_kb(api_key, query, collection, top_k=3):
    """Retrieve matching document chunks from Chroma DB and convert distances to similarity scores."""
    if not collection:
        return []
        
    try:
        # Query ChromaDB (which handles embedding generation automatically via GeminiEmbeddingFunction)
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        chunks = []
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                # Distance representation depends on Chroma distance config (default is L2).
                # To map distance to similarity score:
                # For L2: similarity = 1.0 / (1.0 + distance)
                distance = results['distances'][0][i]
                similarity_score = 1.0 / (1.0 + distance)
                # Keep only 3 decimal places
                similarity_score = round(similarity_score, 3)
                
                chunks.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": similarity_score
                })
        return chunks
    except Exception as e:
        print(f"Retrieval failed: {e}")
        return []

def generate_grounded_response(api_key, query, persona, context_chunks):
    """Generate persona-adapted response strictly grounded in context chunks."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Formulate context text
    context_str = ""
    for i, c in enumerate(context_chunks):
        src = c["metadata"].get("source", "Unknown Source")
        loc = c["metadata"].get("location", "Unknown Section")
        context_str += f"--- SOURCE {i+1}: {src} | Location: {loc} ---\n{c['content']}\n\n"
        
    prompt = f"""You are an enterprise-grade Customer Support AI Agent built with production-ready RAG architecture.
Your purpose is to provide accurate, persona-adapted, emotionally intelligent support while maintaining strict factual grounding.

INCOMING QUERY: "{query}"
DETECTED PERSONA: {persona}

RETRIEVED KNOWLEDGE BASE CONTEXT:
{context_str}

CRITICAL RULES:
1. Base your response ONLY on the provided RETRIEVED KNOWLEDGE BASE CONTEXT above.
2. If the required information is NOT in the context, explicitly state: "I don't have information about [topic] in our current documentation. Let me connect you with a human specialist."
3. Do not make up, extrapolate, or hallucinate any facts.
4. CITE SOURCES: You MUST cite specific source document filenames and page numbers/sections for any claims made (e.g. "According to [api_developer_guide.md] under 'Header Setup'..." or "As described in [billing_and_refund_policy.pdf] Page 1...").

TONE & STYLE ADAPTATION BY PERSONA:
- "Technical Expert": Tone: Precise, systematic, Senior Systems Engineer. Provide configuration specifications, exact parameters, API pathways, code blocks, raw error codes, and step-by-step diagnostic actions. Avoid empathy padding or oversimplification.
- "Frustrated User": Tone: Warm, validating, reassuring, Customer Care Specialist. Begin with IMMEDIATE empathy (e.g. "I understand how frustrating this must be, especially after wasting your valuable time"). Provide 3-5 simple, bulleted cookbook checkmarks. Avoid technical jargon or long explanations.
- "Business Executive": Tone: Professional, outcome-focused, concise. Explain operational implications, SLA protections, business uptime, and estimated resolution timelines. Avoid code blocks, deep configuration parameters, or technical configs.

Generate the response below:
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating response: {e}"

def evaluate_escalation(query, classification, chunks, history=[], conf_threshold=0.45):
    """Check if query triggers escalation based on thresholds, sensitive topics, or frustration."""
    q = query.lower()
    
    # Escalation condition 1: Empty retrieval
    if not chunks:
        return True, "Empty retrieval (no matching documents found)"
        
    # Escalation condition 2: Low confidence
    top_score = chunks[0]["similarity_score"]
    if top_score < conf_threshold:
        return True, f"Retrieval confidence score ({top_score}) is below the threshold ({conf_threshold})"
        
    # Escalation condition 3: Sensitive topics (billing, legal, gdpr, refund, deletion)
    sensitive_words = ["billing", "refund", "credit card", "payment", "bank", "legal", "gdpr", "hipaa", "compliance", "delete account", "delete my account", "account deletion"]
    # Check if query asks for sensitive actions
    matched_word = next((w for w in sensitive_words if w in q), None)
    if matched_word:
        return True, f"Sensitive action/topic detected: [{matched_word}]"
        
    # Escalation condition 4: Explicit human request
    if any(x in q for x in ["human", "support specialist", "talk to someone", "call support", "agent", "representative"]):
        return True, "User explicitly requested human support agent"
        
    # Escalation condition 5: Repeated frustration (3 consecutive turns of Frustrated User persona)
    consecutive_frustration = 0
    if classification["primaryPersona"] == "Frustrated User":
        consecutive_frustration = 1
        for turn in reversed(history):
            if turn.get("persona") == "Frustrated User":
                consecutive_frustration += 1
            else:
                break
    if consecutive_frustration >= 3:
        return True, f"Repeated frustration: User persona classified as Frustrated for {consecutive_frustration} consecutive turns"
        
    # Escalation condition 6: Conflict detection (multiple versions of same document retrieved with conflicting content)
    # Check if we retrieved conflict_demo.md or legacy timeout settings alongside new timeout settings
    retrieved_sources = [c["metadata"].get("source", "") for c in chunks]
    has_legacy = any("legacy" in s for s in retrieved_sources)
    has_new = any("connection_issues" in s for s in retrieved_sources)
    if has_legacy and has_new:
        return True, "Conflict detected: Conflicting document versions (legacy vs current) retrieved simultaneously"

    return False, ""

def generate_handoff_json(query, classification, chunks, history, reason):
    """Generate structured human handoff JSON payload."""
    history_turns = []
    for turn in history:
        history_turns.append({
            "query": turn["query"],
            "response": turn["response"][:120] + "..." if len(turn["response"]) > 120 else turn["response"]
        })
        
    attempted_steps = []
    # Deduce attempted steps from history
    for turn in history:
        if "step" in turn.get("response", "").lower():
            attempted_steps.append("Local self-service diagnostics run")
            break
    if not attempted_steps:
        attempted_steps = ["RAG Knowledge Base Query Search"]
        
    queue = "technical_expert"
    if "billing" in reason.lower() or "refund" in reason.lower():
        queue = "billing_support"
    elif "gdpr" in reason.lower() or "delete" in reason.lower():
        queue = "compliance_desk"
    elif "frustration" in reason.lower():
        queue = "executive_relations_desk"

    handoff = {
        "escalated": True,
        "escalation_reason": reason,
        "confidence_score": chunks[0]["similarity_score"] if chunks else 0.0,
        "handoff_summary": {
            "persona": classification["primaryPersona"],
            "sentiment_score": classification["sentiment"],
            "emotion": classification["emotion"],
            "urgency": classification["urgency"],
            "detected_issue": query[:150],
            "language": classification["language"],
            "conversation_turns": len(history) + 1,
            "previous_history": history_turns,
            "documents_used": list(set([c["metadata"].get("source", "unknown") for c in chunks])),
            "attempted_steps": attempted_steps,
            "recommendation": get_recommendation_for_queue(queue),
            "suggested_escalation_queue": queue
        }
    }
    return handoff

def get_recommendation_for_queue(queue):
    if queue == "billing_support":
        return "Review payment gateway transaction status and inspect refund eligibility criteria."
    elif queue == "compliance_desk":
        return "Process GDPR deletion token, purge PII records, and verify compliance audits."
    elif queue == "executive_relations_desk":
        return "Initiate direct client relations callback, offer service credit SLA compensation."
    return "Check host configuration settings and evaluate API request log traces."
