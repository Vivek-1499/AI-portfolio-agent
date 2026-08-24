import streamlit as st
from graph import portfolio_graph

# Page Configuration
st.set_page_config(
    page_title="Vivek Kumar Pandit | AI Portfolio Assistant",
    page_icon="💼",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-text {
        font-size: 1.05rem;
        color: #6c757d;
        margin-bottom: 1.5rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 75%;
        font-weight: 700;
        border-radius: 0.25rem;
        background-color: #f0f2f6;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Main Title Section
st.markdown('<div class="main-header">💼 Vivek Kumar Pandit — AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<br>', unsafe_allow_html=True)

# Sidebar with Profile Info and Presets
with st.sidebar:
    st.header("👨‍💻 About Vivek")
    st.write("**Full-Stack | SDE**")
    st.write("📍 Mumbai, India")
    st.write("🎓 B.Tech IT — KJ Somaiya College of Engg (GPA: 8.75)")
    
    st.markdown("---")
    st.subheader("📬 Contact & Socials")
    st.write("📧 [vivek.pandit1499@gmail.com](mailto:vivek.pandit1499@gmail.com)")
    st.write("🔗 [LinkedIn Profile](https://www.linkedin.com/in/vivek-pandit-368b012a7/)")
    st.write("💻 [GitHub Profile](https://github.com/Vivek-1499)")
    
    st.markdown("---")
    st.subheader("💡 Sample Inquiries")
    
    if st.button("🚀 What are Vivek's top projects?"):
        st.session_state["user_input_preset"] = "Can you summarize Vivek's key projects and their technical architecture?"
    if st.button("🛠️ About Vivek?"):
        st.session_state["user_input_preset"] = "Can you provide Vivek's professional summary, and list the names and roles of the companies where he completed his internships?"
    if st.button("🎓 Education & Core Skills"):
        st.session_state["user_input_preset"] = "What is Vivek's educational background and primary technical stack?"
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

# Initialize Chat Memory
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant", 
            "content": "Hello! I am Vivek's AI Portfolio Assistant. Ask me anything about his projects, work experience, technical stack, or background!"
        }
    ]

# Render Message Stream
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Process Input
preset_query = st.session_state.pop("user_input_preset", None)
user_query = st.chat_input("Ask about Vivek's experience, skills, or projects...") or preset_query

if user_query:
    # 1. Display User Message
    st.session_state["messages"].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Run LangGraph with Live Step Trace
    with st.chat_message("assistant"):
        with st.status("🧠 Agent Reasoning & State Machine...", expanded=True) as status:
            initial_state = {
                "question": user_query,
                "documents": [],
                "web_search_needed": "No",
                "route": "",
                "generation": ""
            }
            
            final_generation = ""
            current_state = initial_state.copy()
            
            # event contains that node's state update if used stream_mode="updates".
            for event in portfolio_graph.stream(initial_state, stream_mode="updates"):
                for node_name, node_state in event.items():
                    current_state.update(node_state)
                    
                    if node_name == "route_query":
                        st.write(f"🧭 **Router Decision:** Intent identified as `{node_state.get('route')}`")
                    elif node_name == "retrieve_resume":
                        st.write(f"📄 **Portfolio RAG:** Retrieved {len(node_state.get('documents', []))} verified context chunks from FAISS.")
                    elif node_name == "grade_documents":
                        needed = node_state.get("web_search_needed")
                        st.write(f"⚖️ **Self-RAG Grader:** Context relevance verified? `{'No (Triggering Web Fallback)' if needed == 'Yes' else 'Yes'}`")
                    elif node_name == "conduct_web_search":
                        st.write(f"🌐 **Web Search Executed:** Sourced real-time web context via DuckDuckGo.")
                    elif node_name == "generate_answer":
                        final_generation = node_state.get("generation", "")
                        
            status.update(label="✅ Response Generated", state="complete", expanded=False)

        # 3. Output Response
        st.markdown(final_generation)
        st.session_state["messages"].append({"role": "assistant", "content": final_generation})