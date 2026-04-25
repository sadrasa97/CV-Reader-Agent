"""
Streamlit UI for CV Reader Agent Pipeline
"""
import streamlit as st
import requests
import time
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="AI CV Reader & Candidate Analysis",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.3rem;
        color: #2ca02c;
        font-weight: bold;
        border-bottom: 2px solid #2ca02c;
        padding-bottom: 10px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 5px solid #f5424a;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# API configuration
API_BASE = os.getenv("API_URL", "http://localhost:8000")

# Session state initialization
if "uploaded_tasks" not in st.session_state:
    st.session_state.uploaded_tasks = {}

if "query_history" not in st.session_state:
    st.session_state.query_history = []


def check_api_health():
    """Check if API is available"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def upload_cv(file, progress_bar=None):
    """Upload a CV file"""
    try:
        if progress_bar:
            progress_bar.progress(20)
        
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{API_BASE}/upload", files=files, timeout=30)
        
        if progress_bar:
            progress_bar.progress(100)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Upload failed")}
    except Exception as e:
        return {"error": str(e)}


def check_task_status(task_id):
    """Check the status of a processing task"""
    try:
        response = requests.get(f"{API_BASE}/task/{task_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Task not found"}
    except Exception as e:
        return {"error": str(e)}


def query_agent(question, top_k=5):
    """Send a query to the HR agent"""
    try:
        payload = {"question": question, "top_k": top_k}
        response = requests.post(f"{API_BASE}/query", json=payload, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Query failed")}
    except Exception as e:
        return {"error": str(e)}


def list_candidates():
    """Get list of all candidates"""
    try:
        response = requests.get(f"{API_BASE}/candidates", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to fetch candidates"}
    except Exception as e:
        return {"error": str(e)}


def delete_candidate(candidate_id):
    """Delete a candidate"""
    try:
        response = requests.delete(f"{API_BASE}/candidates/{candidate_id}", timeout=10)
        if response.status_code == 200:
            return {"status": "ok"}
        else:
            return {"error": "Failed to delete candidate"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Main UI Layout
# ============================================================================

st.markdown('<h1 class="main-header">📄 AI CV Reader & Candidate Analysis</h1>', unsafe_allow_html=True)
st.markdown("*Production-ready pipeline with LangChain Agent & Function Calling*")

# Check API status
if not check_api_health():
    st.error("❌ API is not available. Please ensure the FastAPI server is running on http://localhost:8000")
    st.info("Run the server with: `uvicorn app.main:app --reload`")
    st.stop()

st.success("✅ API is running")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📤 Upload CVs", "💬 Query Agent", "👥 Candidates", "📊 Analytics", "⚙️ Settings"]
)

# ============================================================================
# Tab 1: Upload CVs
# ============================================================================
with tab1:
    st.markdown('<h2 class="section-header">Upload CVs for Processing</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Upload one or multiple CVs (PDF or DOCX)**")
        uploaded_files = st.file_uploader(
            "Choose CV files",
            accept_multiple_files=True,
            type=["pdf", "docx"],
            key="cv_uploader"
        )
    
    with col2:
        st.markdown("**Upload Status**")
        status_placeholder = st.empty()
    
    if uploaded_files:
        st.divider()
        
        # Process each file
        for file in uploaded_files:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**{file.name}** ({file.size / 1024:.1f} KB)")
            
            with col2:
                progress_bar = st.progress(0)
            
            # Upload file
            result = upload_cv(file, progress_bar)
            
            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                candidate_id = result.get("candidate_id", "")
                task_id = result.get("task_id", "")
                
                # Store task info
                st.session_state.uploaded_tasks[task_id] = {
                    "filename": file.name,
                    "candidate_id": candidate_id,
                    "uploaded_at": datetime.now().isoformat()
                }
                
                st.success(f"✅ Uploaded! Candidate ID: `{candidate_id}`")
                st.info(f"🔄 Processing... Task ID: `{task_id}`")
        
        st.divider()
        
        # Task monitoring
        st.markdown("**Active Processing Tasks**")
        
        if st.session_state.uploaded_tasks:
            # Create placeholder for task updates
            task_container = st.container()
            
            with task_container:
                for task_id, task_info in list(st.session_state.uploaded_tasks.items()):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{task_info['filename']}**")
                    
                    # Check task status
                    status_result = check_task_status(task_id)
                    
                    if "error" not in status_result:
                        status = status_result.get("status", "UNKNOWN")
                        progress = status_result.get("progress", 0)
                        
                        with col2:
                            st.write(f"Status: **{status}**")
                        
                        with col3:
                            if status == "SUCCESS":
                                st.success("✅ Complete")
                                # Remove from tracking
                                del st.session_state.uploaded_tasks[task_id]
                            elif status == "FAILED":
                                st.error("❌ Failed")
                                error = status_result.get("error", "Unknown error")
                                st.error(f"Error: {error}")
                            else:
                                st.progress(progress / 100)
        else:
            st.info("No active tasks. Upload CVs to get started.")


# ============================================================================
# Tab 2: Query Agent
# ============================================================================
with tab2:
    st.markdown('<h2 class="section-header">Query HR Agent</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    Ask questions about candidates. The agent will automatically:
    - Search for matching candidates
    - Compare candidates based on criteria
    - Provide structured analysis
    
    **Example queries:**
    - "Who is the best fit for Senior Python Backend Engineer with AWS?"
    - "Compare candidates for Data Science role"
    - "Show me all candidates with Machine Learning experience"
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query_text = st.text_area(
            "Your question",
            placeholder="e.g., Who is the best fit for Senior Python Backend Engineer with AWS experience?",
            height=100,
            key="query_input"
        )
    
    with col2:
        top_k = st.slider("Top K results", 1, 20, 5, key="topk_slider")
        submit_btn = st.button("🔍 Analyze", use_container_width=True)
    
    if submit_btn:
        if not query_text.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("🤔 Agent is reasoning and calling tools..."):
                result = query_agent(query_text, top_k)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    # Store in history
                    st.session_state.query_history.append({
                        "query": query_text,
                        "timestamp": datetime.now().isoformat(),
                        "result": result
                    })
                    
                    # Display results
                    st.divider()
                    st.markdown("### 📊 Agent Response")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Tool Used:** `{result.get('tool_used', 'N/A')}`")
                    
                    with col2:
                        st.markdown(f"**Candidates Found:** `{result.get('candidates_found', 0)}`")
                    
                    st.divider()
                    
                    # Main response
                    st.markdown("**Agent Analysis:**")
                    st.info(result.get("answer", "No response from agent"))
                    
                    # Structured results
                    if result.get("structured_results"):
                        st.markdown("**Structured Candidate Matches:**")
                        
                        for idx, match in enumerate(result["structured_results"], 1):
                            with st.expander(
                                f"#{idx} - {match.get('metadata', {}).get('name', 'Unknown')} "
                                f"({match.get('candidate_id')})"
                            ):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Relevance Score:** {match.get('relevance_score', 0):.2%}")
                                    st.write(f"**Email:** {match.get('metadata', {}).get('email', 'N/A')}")
                                
                                with col2:
                                    st.write(f"**Years Exp:** {match.get('metadata', {}).get('years_experience', 'N/A')}")
                                    skills = match.get('metadata', {}).get('skills', [])
                                    if skills:
                                        st.write(f"**Skills:** {', '.join(skills[:5])}")
                                
                                st.write(f"**Evidence:** {match.get('evidence', 'N/A')}")
                    
                    # Reasoning
                    if result.get("reasoning"):
                        st.markdown("**Agent Reasoning:**")
                        st.caption(result["reasoning"])
    
    # Query history
    if st.session_state.query_history:
        st.divider()
        st.markdown("**Recent Queries**")
        
        for i, h in enumerate(st.session_state.query_history[-5:], 1):
            with st.expander(f"{i}. {h['query'][:50]}..."):
                st.write(f"Result: {h['result'].get('answer', 'N/A')[:200]}...")


# ============================================================================
# Tab 3: Candidates
# ============================================================================
with tab3:
    st.markdown('<h2 class="section-header">Candidate Database</h2>', unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Candidates", use_container_width=True):
        st.rerun()
    
    result = list_candidates()
    
    if "error" in result:
        st.error(f"Error loading candidates: {result['error']}")
    else:
        total = result.get("total_candidates", 0)
        candidates = result.get("candidates", [])
        
        st.markdown(f"**Total Candidates:** `{total}`")
        st.divider()
        
        if total == 0:
            st.info("No candidates in the database. Upload CVs to get started.")
        else:
            # Create a table view
            for idx, candidate in enumerate(candidates, 1):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(
                        f"**{idx}. {candidate.get('name', 'Unknown')}**\n"
                        f"`{candidate['candidate_id']}`"
                    )
                
                with col2:
                    email = candidate.get('email', 'N/A')
                    years = candidate.get('years_experience', 'N/A')
                    skills = ", ".join(candidate.get('skills', [])[:4])
                    
                    st.write(
                        f"📧 {email}\n"
                        f"⏱️ {years} years experience\n"
                        f"🔧 {skills}"
                    )
                
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{candidate['candidate_id']}"):
                        delete_result = delete_candidate(candidate['candidate_id'])
                        if "error" not in delete_result:
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")
                
                st.divider()


# ============================================================================
# Tab 4: Analytics
# ============================================================================
with tab4:
    st.markdown('<h2 class="section-header">Pipeline Analytics</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    result = list_candidates()
    total_candidates = result.get("total_candidates", 0) if "error" not in result else 0
    
    with col1:
        st.metric("Total Candidates", total_candidates)
    
    with col2:
        st.metric("CVs Processed", len(st.session_state.uploaded_tasks) + total_candidates)
    
    with col3:
        st.metric("Queries Executed", len(st.session_state.query_history))
    
    st.divider()
    st.markdown("**Recent Activity**")
    
    if st.session_state.query_history:
        st.write("Latest queries:")
        for h in st.session_state.query_history[-3:]:
            st.write(f"- {h['query']}")
    else:
        st.info("No query history yet.")


# ============================================================================
# Tab 5: Settings
# ============================================================================
with tab5:
    st.markdown('<h2 class="section-header">Settings & Configuration</h2>', unsafe_allow_html=True)
    
    st.markdown("**API Configuration**")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        api_url = st.text_input("API Base URL", value=API_BASE)
    
    with col2:
        if st.button("🔗 Test Connection"):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Connected!")
                else:
                    st.error("❌ Connection failed")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    st.markdown("**Database Management**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All CVs", use_container_width=True):
            try:
                response = requests.post(f"{API_BASE}/reset", timeout=10)
                if response.status_code == 200:
                    st.success("✅ Database cleared!")
                    st.rerun()
                else:
                    st.error("Failed to clear database")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("📊 Export Analytics", use_container_width=True):
            st.info("Export feature coming soon!")
    
    st.divider()
    
    st.markdown("**Debug Information**")
    
    if st.checkbox("Show debug info"):
        st.write(f"API URL: `{API_BASE}`")
        st.write(f"Active tasks: `{len(st.session_state.uploaded_tasks)}`")
        st.write(f"Query history: `{len(st.session_state.query_history)}`")
        
        # Health check details
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            st.write("**Health Check Result:**")
            st.json(response.json())
        except Exception as e:
            st.error(f"Health check failed: {str(e)}")

st.divider()
st.markdown("*CV Reader Agent Pipeline v1.0.0 • Powered by FastAPI + LangChain + ChromaDB + Ollama*")
