import os
import streamlit as st
import json
from dotenv import load_dotenv

# Import our custom modules
from agent import get_chroma_collection, classify_persona, retrieve_kb, generate_grounded_response, evaluate_escalation, generate_handoff_json
from ingest import ingest_to_chroma

# Load local environment variables if available
load_dotenv()

# App Page Layout
st.set_page_config(
    page_title="Persona-Adaptive Customer Support Agent (RAG)",
    page_icon="🤖",
    layout="wide"
)

# Custom Styles for dark theme alignment
st.markdown("""
<style>
    .badge-technical {
        background-color: rgba(0, 242, 254, 0.15);
        color: #00f2fe;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid rgba(0, 242, 254, 0.3);
        font-weight: bold;
    }
    .badge-frustrated {
        background-color: rgba(255, 65, 108, 0.15);
        color: #ff416c;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid rgba(255, 65, 108, 0.3);
        font-weight: bold;
    }
    .badge-executive {
        background-color: rgba(245, 175, 25, 0.15);
        color: #f5af19;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid rgba(245, 175, 25, 0.3);
        font-weight: bold;
    }
    .escalated-box {
        background-color: rgba(255, 65, 108, 0.05);
        border-left: 5px solid #ff416c;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "last_classification" not in st.session_state:
    st.session_state.last_classification = None
if "last_chunks" not in st.session_state:
    st.session_state.last_chunks = []
if "last_escalation" not in st.session_state:
    st.session_state.last_escalation = {"status": False, "reason": ""}

# Sidebar Config
st.sidebar.header("🔑 API & Model Configuration")

# API Key Input
api_key = st.sidebar.text_input(
    "Google Gemini API Key",
    type="password",
    value=os.getenv("GEMINI_API_KEY", ""),
    help="Provide your Google Gemini developer API Key. Get one at ai.google.dev."
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ RAG Hyperparameters")

# Thresholds
conf_threshold = st.sidebar.slider(
    "Similarity Confidence Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.45,
    step=0.05,
    help="Minimum similarity score required to trust retrieved context chunks. Anything below triggers escalation."
)

top_k = st.sidebar.slider(
    "Top-K Chunks to Retrieve",
    min_value=1,
    max_value=5,
    value=3
)

st.sidebar.markdown("---")
st.sidebar.header("📁 Knowledge Base Ingestion")

# KB Info
data_dir = "docs/data"
persist_dir = "chroma_db"
docs_present = os.path.exists(data_dir) and len(os.listdir(data_dir)) > 0 if os.path.exists(data_dir) else False

if docs_present:
    num_files = len(os.listdir(data_dir))
    st.sidebar.success(f"Support documents found: {num_files} files in `docs/data/`.")
else:
    st.sidebar.warning("No support documents found in `docs/data/`. Please run the generator first.")

# Ingestion trigger
if st.sidebar.button("Ingest / Re-Ingest Documents"):
    if not api_key:
        st.sidebar.error("Gemini API key is required to embed documents!")
    else:
        with st.sidebar.spinner("Running document ingestion pipeline..."):
            try:
                # Dynamically run mock data script if empty to ensure docs exist
                if not docs_present:
                    import subprocess
                    subprocess.run(["python", "create_mock_data.py"], check=True)
                
                num_chunks = ingest_to_chroma(api_key, data_dir, persist_dir)
                st.sidebar.success(f"Successfully indexed {num_chunks} chunks into ChromaDB!")
                # Rerun to update file counts
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Ingestion failed: {e}")

# Application Main Title
st.title("🤖 Persona-Adaptive Customer Support Agent")
st.markdown("An enterprise-grade Customer Support Assistant using LLMs, Retrieval-Augmented Generation (RAG), and configurable Escalation Logic.")

# Check database collection
db_collection = None
if api_key:
    db_collection = get_chroma_collection(api_key, persist_dir)
    if db_collection:
        try:
            db_count = db_collection.count()
            st.info(f"💾 Vector Database Connected. ChromaDB Collection `support_kb` contains {db_count} active chunks.")
        except Exception:
            st.warning("⚠️ ChromaDB exists but collection is not initialized. Please click Ingest Documents in the sidebar.")
    else:
        st.warning("⚠️ ChromaDB has not been created yet. Please enter your API Key and click 'Ingest / Re-Ingest Documents' in the sidebar.")
else:
    st.error("❗ Please enter your Google Gemini API Key in the sidebar to authenticate model workflows.")

# Layout Columns
col_chat, col_inspect = st.columns([3, 2])

with col_chat:
    st.subheader("💬 Customer Chat Interface")
    
    # Preset scenarios helper
    st.write("Quick Test Scenarios:")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    preset_query = ""
    
    if c1.button("Technical"):
        preset_query = "Can you explain the API authentication failure and provide config setup details for the Authorization Bearer header?"
    if c2.button("Frustrated"):
        preset_query = "THIS CONVERSION MODULE IS A TOTAL DISASTER! I HAVE WASTED THREE HOURS AND IT IS URGENT! DO SOMETHING NOW!!!"
    if c3.button("Executive"):
        preset_query = "What are the SLA compensation credits if monthly uptime drops below 99.9%? When will port 8080 updates resolve?"
    if c4.button("Refund"):
        preset_query = "Please delete my account GDPR logs and process a refund for my last invoice, it's very important."
    if c5.button("Conflict"):
        preset_query = "What database connection timeout threshold is recommended to configure?"
    if c6.button("Out-of-Scope"):
        preset_query = "How do you cook a perfect Italian pasta carbonara?"

    # Display Chat Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"])
            else:
                if msg.get("escalated", False):
                    st.markdown("⚠️ **SYSTEM ESCALATED TO HUMAN SUPPORT AGENT**")
                    st.json(msg["content"])
                else:
                    st.write(msg["content"])

    # User Input
    user_query = st.chat_input("Type customer support query here...")
    
    # Handle Preset Trigger
    if preset_query:
        user_query = preset_query

    if user_query:
        if not api_key:
            st.error("API Key missing! Please enter your key in the sidebar.")
        elif not db_collection:
            st.error("Vector database connection missing! Please ingest documents first.")
        else:
            # Append User message
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            with st.spinner("Processing Agent Pipeline (Persona → RAG → Verification → Output)..."):
                # Step 1 & 2: Classify Persona
                classification = classify_persona(api_key, user_query, st.session_state.history)
                st.session_state.last_classification = classification
                
                # Step 3: Retrieve Context Chunks
                retrieved_chunks = retrieve_kb(api_key, user_query, db_collection, top_k)
                st.session_state.last_chunks = retrieved_chunks
                
                # Step 4: Evaluate Escalation
                is_escalated, escalation_reason = evaluate_escalation(
                    user_query, 
                    classification, 
                    retrieved_chunks, 
                    st.session_state.history, 
                    conf_threshold
                )
                
                agent_response = None
                
                if is_escalated:
                    # Step 5: Escalated Handoff JSON
                    handoff_data = generate_handoff_json(
                        user_query, 
                        classification, 
                        retrieved_chunks, 
                        st.session_state.history, 
                        escalation_reason
                    )
                    st.session_state.last_escalation = {"status": True, "reason": escalation_reason}
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": handoff_data,
                        "escalated": True
                    })
                    agent_response = json.dumps(handoff_data)
                else:
                    # Step 5: Generate grounded response
                    st.session_state.last_escalation = {"status": False, "reason": ""}
                    response_text = generate_grounded_response(
                        api_key, 
                        user_query, 
                        classification["primaryPersona"], 
                        retrieved_chunks
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "escalated": False
                    })
                    agent_response = response_text
                
                # Update history
                st.session_state.history.append({
                    "query": user_query,
                    "persona": classification["primaryPersona"],
                    "response": agent_response
                })
            
            st.rerun()

    # Reset History Button
    if st.button("Clear Conversation History"):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.last_classification = None
        st.session_state.last_chunks = []
        st.session_state.last_escalation = {"status": False, "reason": ""}
        st.rerun()

with col_inspect:
    st.subheader("🕵️ RAG & Persona Inspector")
    
    # 1. Timeline Step Execution
    st.markdown("### ⚙️ Pipeline Execution Status")
    if st.session_state.last_classification:
        st.success("✅ **Step 1:** Parsed message and history")
        st.success("✅ **Step 2:** Classified persona attributes")
        st.success(f"✅ **Step 3:** Retrieved top-{top_k} vector chunks")
        st.success("✅ **Step 4:** Evaluated retrieval quality scores")
        
        esc_status = st.session_state.last_escalation["status"]
        if esc_status:
            st.warning(f"⚠️ **Step 5:** Escalation triggered! Reason: {st.session_state.last_escalation['reason']}")
            st.success("✅ **Step 6:** Assembled human handoff JSON")
        else:
            st.success("✅ **Step 5:** Selected tone-adapted prompt template")
            st.success("✅ **Step 6:** Compiled context chunks and user query")
            st.success("✅ **Step 7:** Generated grounded response")
            st.success("✅ **Step 8:** Completed factual grounding validations")
    else:
        st.write("Send a customer query to see real-time pipeline telemetry.")
        
    # 2. Persona Breakdown
    st.markdown("### 📊 Persona Classification")
    if st.session_state.last_classification:
        cl = st.session_state.last_classification
        
        # Display Persona Badge
        if cl["primaryPersona"] == "Technical Expert":
            st.markdown(f"Primary Persona: <span class='badge-technical'>Technical Expert</span>", unsafe_allow_html=True)
        elif cl["primaryPersona"] == "Frustrated User":
            st.markdown(f"Primary Persona: <span class='badge-frustrated'>Frustrated User</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"Primary Persona: <span class='badge-executive'>Business Executive</span>", unsafe_allow_html=True)
            
        # Metrics Table
        st.write("")
        c_sent, c_emo = st.columns(2)
        c_sent.metric("Sentiment Score", cl["sentiment"])
        c_emo.metric("Detected Emotion", cl["emotion"])
        
        c_urg, c_comp = st.columns(2)
        c_urg.metric("Urgency Level", cl["urgency"])
        c_comp.metric("Complexity Class", cl["complexity"])
        
        st.metric("Auto-Detected Language", cl["language"])
    else:
        st.write("No classification parsed yet.")

    # 3. Retrieved Documents Table
    st.markdown("### 📚 Retrieved Context Chunks")
    if st.session_state.last_chunks:
        for idx, chunk in enumerate(st.session_state.last_chunks):
            with st.expander(f"Chunk {idx+1} (Score: {chunk['similarity_score']})"):
                st.markdown(f"**Source:** `{chunk['metadata'].get('source')}` | **Location:** `{chunk['metadata'].get('location')}`")
                st.code(chunk["content"], language="markdown")
                
                # Check threshold pass/fail
                if chunk["similarity_score"] >= conf_threshold:
                    st.success(f"Similarity {chunk['similarity_score']} >= {conf_threshold} (Threshold Pass)")
                else:
                    st.error(f"Similarity {chunk['similarity_score']} < {conf_threshold} (Threshold Fail)")
    else:
        st.write("No documents retrieved.")
