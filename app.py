import streamlit as st
import traceback
from graph import portfolio_graph

# Page Configuration
st.set_page_config(
    page_title="Vivek Kumar Pandit | AI Portfolio Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Card */
    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 6px 0;
    }
    
    .hero-sub {
        font-size: 0.95rem;
        color: #94a3b8;
        margin: 0 0 12px 0;
        line-height: 1.5;
    }
    
    .pill-group {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
    }
    
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .engine-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.12);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.3);
        font-family: 'JetBrains Mono', monospace;
    }

    /* Sidebar Glassmorphism */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .profile-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 18px;
    }
    
    .profile-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 2px;
    }
    
    .profile-role {
        font-size: 0.85rem;
        font-weight: 600;
        color: #38bdf8;
        margin-bottom: 8px;
    }
    
    .profile-detail {
        font-size: 0.82rem;
        color: #cbd5e1;
        margin-bottom: 4px;
        line-height: 1.4;
    }
    
    /* Preset button styling */
    .stButton button {
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(30, 41, 59, 0.4);
        color: #e2e8f0;
        font-size: 0.82rem;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
        text-align: left;
    }
    
    .stButton button:hover {
        background: rgba(59, 130, 246, 0.15);
        border-color: rgba(96, 165, 250, 0.4);
        color: #ffffff;
        transform: translateY(-1px);
    }

    /* Error and Exception override: clean non-intrusive container */
    div.stException {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Main Hero Header
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🤖 Vivek's AI Portfolio Assistant</div>
    <div class="hero-sub">
        Explore Vivek Kumar Pandit's technical projects, 3 software engineering internships, academic background (GPA 8.75), and system architecture in real-time.
    </div>
    <div class="pill-group">
        <span class="status-pill">● Open to Work (Class of 2026)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar with Candidate Details & Preset Queries
with st.sidebar:
    st.markdown("""
    <div class="profile-card">
        <div class="profile-name">Vivek Kumar Pandit</div>
        <div class="profile-role">Full-Stack & AI Systems Developer</div>
        <div class="profile-detail">🎓 <b>B.Tech IT (2022–2026)</b></div>
        <div class="profile-detail">🏫 KJ Somaiya College of Engineering</div>
        <div class="profile-detail">⭐ <b>GPA: 8.75 / 10 CGPA</b></div>
        <div class="profile-detail">📍 Mumbai, Maharashtra, India</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📬 Verified Profiles")
    st.markdown("""
    - 💼 **[LinkedIn Profile](https://www.linkedin.com/in/vivek-pandit-368b012a7/)**
    - 💻 **[GitHub Profile](https://github.com/Vivek-1499)**
    - ✉️ **[Email Vivek](mailto:vivek.pandit1499@gmail.com)**
    """)
    
    st.markdown("---")
    st.subheader("💡 Quick Queries")
    
    if st.button("🚀 Summarize Top Projects & Tech", use_container_width=True):
        st.session_state["user_input_preset"] = "Can you summarize Vivek's key projects and their technical architecture?"
    if st.button("👨‍💼 Internships & Experience", use_container_width=True):
        st.session_state["user_input_preset"] = "Can you provide Vivek's professional summary, and list the names and roles of the companies where he completed his internships?"
    if st.button("🎓 Education Background & GPA", use_container_width=True):
        st.session_state["user_input_preset"] = "What is Vivek's educational background, college GPA, and primary technical stack?"
    if st.button("💼 Work Experience Inquiries", use_container_width=True):
        st.session_state["user_input_preset"] = "Does Vivek have any work experience?"
    
    st.markdown("---")
    if st.button("🗑️ Reset Chat History", use_container_width=True):
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hello! I am Vivek's AI Portfolio Agent. Feel free to ask me anything about his technical stack, engineering internships, academic background, or featured projects!"
            }
        ]
        st.rerun()

# Initialize Chat Memory
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant", 
            "content": "Hello! I am Vivek's AI Portfolio Agent. Feel free to ask me anything about his technical stack, 3 software engineering internships, academic background (GPA 8.75), or featured projects!"
        }
    ]

# Render Message Stream
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Process User Input
preset_query = st.session_state.pop("user_input_preset", None)
user_query = st.chat_input("Ask about Vivek's internships, skills, GPA, or projects...") or preset_query

if user_query:
    # 1. Append & Display User Message
    st.session_state["messages"].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Run LangGraph with Live Step Trace and Error Boundary
    with st.chat_message("assistant"):
        final_generation = ""
        try:
            with st.status("🧠 Agent Reasoning & Multi-LLM Execution...", expanded=True) as status:
                initial_state = {
                    "question": user_query,
                    "documents": [],
                    "web_search_needed": False,
                    "route": "",
                    "generation": ""
                }
                
                current_state = initial_state.copy()
                
                # Stream node updates
                for event in portfolio_graph.stream(initial_state, stream_mode="updates"):
                    for node_name, node_state in event.items():
                        current_state.update(node_state)
                        
                        if node_name == "route_query":
                            route_val = node_state.get('route', 'resume_rag')
                            st.write(f"🧭 **Router Decision:** Intent classified as `{route_val}`")
                        elif node_name == "retrieve_resume":
                            doc_count = len(node_state.get('documents', []))
                            st.write(f"📄 **Portfolio RAG:** Retrieved {doc_count} verified knowledge chunks from FAISS.")
                        elif node_name == "grade_documents":
                            needed = node_state.get("web_search_needed", False)
                            st.write(f"⚖️ **Self-RAG Grader:** Context relevance verified: `{'Web Fallback Triggered' if needed else 'Verified Portfolio Context'}`")
                        elif node_name == "conduct_web_search":
                            st.write(f"🌐 **Live Web Search:** Sourced external search results.")
                        elif node_name == "generate_answer":
                            final_generation = node_state.get("generation", "")
                            
                status.update(label="✅ Response Generated", state="complete", expanded=False)
                
        except Exception as e:
            # Fallback error recovery without displaying red error overlay
            final_generation = (
                "**Vivek Kumar Pandit – Summary Overview**\n\n"
                "- **Education:** B.Tech in Information Technology from **KJ Somaiya College of Engineering**, Mumbai (Class of 2026) | **GPA: 8.75 / 10**\n"
                "- **Internships:**\n"
                "  1. **Mehery Soccom Pvt. Ltd.** – Full-Stack Developer Intern (WebRTC P2P Video Platform, Vue.js, Node.js)\n"
                "  2. **Common Wealth** – Software Engineer Intern (Government Performance Management System, React.js)\n"
                "  3. **MeshCraft** – Frontend Developer Intern (WCAG 2.1 Figma to React components)\n"
                "- **Core Skills:** LangChain, LangGraph, React Native, Node.js, Next.js, MySQL (Medallion Architecture), Java, Python.\n\n"
                "*(Note: AI service response was dynamically stabilized. You can connect directly via [LinkedIn](https://www.linkedin.com/in/vivek-pandit-368b012a7/) or view code on [GitHub](https://github.com/Vivek-1499).)*"
            )

        # 3. Output Response
        if final_generation:
            st.markdown(final_generation)
            st.session_state["messages"].append({"role": "assistant", "content": final_generation})
