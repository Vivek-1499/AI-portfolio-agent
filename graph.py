import os
from typing import List, TypedDict
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import StateGraph, START, END

# 1. Environment & Multi-LLM Setup with Priority Fallbacks
load_dotenv()

def build_resilient_llm():
    """Builds a primary LLM with fallback cascade: Groq -> DeepSeek -> OpenAI -> Gemini."""
    models = []
    
    # 1. Groq (Primary & Fast Fallback) - Highest throughput & token limit
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        models.append(ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=groq_api_key))
        models.append(ChatGroq(model="openai/gpt-oss-20b", temperature=0.1, api_key=groq_api_key))
    
    # 2. DeepSeek (Fallback 1)
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_api_key:
        models.append(ChatOpenAI(
            model="deepseek-chat",
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com",
            temperature=0.1
        ))
        
    # 3. OpenAI (Fallback 2)
    openai_api_key = os.getenv("OPEN_API_KEY") or os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        models.append(ChatOpenAI(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            temperature=0.1
        ))
        
    # 4. Google Gemini (Fallback 3)
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        models.append(ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=gemini_api_key,
            temperature=0.1
        ))

    if not models:
        # Fallback dummy if no keys are set
        return ChatGroq(model="openai/gpt-oss-120b", temperature=0.1)

    primary_model = models[0]
    if len(models) > 1:
        return primary_model.with_fallbacks(models[1:])
    return primary_model

llm = build_resilient_llm()

# 2. Ingest Corpus & Build Vector Store with Section Preservation & Network Safeguard
loader = TextLoader("./corpus.txt", encoding="utf-8")
docs = loader.load()

# Use larger chunks to keep entire sections (Education, Internships, Projects) intact
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " "]
)
chunks = text_splitter.split_documents(docs)

# Safe Vector Store initialization with fallback
retriever = None
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vector_store = FAISS.from_documents(chunks, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 6})
except Exception as e:
    retriever = None

web_search_tool = DuckDuckGoSearchRun()


# 3. Define Graph State
class PortfolioState(TypedDict):
    question: str
    route: str
    documents: List[str]
    web_search_needed: bool
    generation: str


# 4. Graph Nodes
def route_query(state: PortfolioState):
    """Routes inquiry to either resume knowledge base, external web, or direct conversation."""
    question = state["question"]
    
    # Fast heuristic check to ensure all personal queries stay in resume_rag
    q_lower = question.lower()
    personal_keywords = [
        "vivek", "project", "experience", "internship", "education", "college",
        "somaiya", "gpa", "degree", "skill", "stack", "tech", "contact",
        "email", "linkedin", "github", "work", "role", "summary", "about", "resume", "who"
    ]
    if any(k in q_lower for k in personal_keywords):
        return {"route": "resume_rag"}
    
    prompt = PromptTemplate(
        template="""You are an AI intent classifier for Vivek Kumar Pandit's portfolio website.
Classify the visitor's question into EXACTLY ONE category:
- 'resume_rag': For questions regarding Vivek's skills, projects, experience, internships, education, GPA, college, contact info, background, or summary.
- 'web_search': For external tech news, current industry market salaries, or external tools unrelated to Vivek.
- 'general_chat': For casual greetings (e.g., 'hello', 'hi', 'how are you', 'what can you do').

Return ONLY the category name.

Inquiry: {question}
Category:""",
        input_variables=["question"]
    )
    
    try:
        router_chain = prompt | llm | StrOutputParser()
        decision = router_chain.invoke({"question": question}).strip().lower()
    except Exception:
        decision = "resume_rag"
    
    if "resume" in decision or "rag" in decision:
        decision = "resume_rag"
    elif "web" in decision:
        decision = "web_search"
    else:
        decision = "general_chat"
        
    return {"route": decision}


def retrieve_resume(state: PortfolioState):
    """Retrieves relevant chunks from Vivek's portfolio corpus."""
    question = state["question"]
    doc_strings = []
    if retriever is not None:
        try:
            retrieved_docs = retriever.invoke(question)
            doc_strings = [doc.page_content for doc in retrieved_docs]
        except Exception:
            doc_strings = []
            
    if not doc_strings:
        # Resilient fallback: return full verified corpus text if vector search encounters any network glitch
        doc_strings = [docs[0].page_content]
        
    return {"documents": doc_strings}


def grade_documents(state: PortfolioState):
    """Self-RAG Grader: Checks if retrieved resume context is sufficient."""
    route = state.get("route", "")
    # For portfolio / personal inquiries about Vivek, NEVER trigger generic web search (to prevent context poisoning)
    if route == "resume_rag":
        return {"web_search_needed": False}
        
    question = state["question"]
    docs_text = "\n\n".join(state.get("documents", []))
    
    prompt = PromptTemplate(
        template="""You are a strict relevance grader.
Determine if the retrieved context contains sufficient facts to answer the question.

Retrieved Context:
{docs}

Question:
{question}

Respond ONLY with 'YES' if relevant and helpful, or 'NO' if external search is needed.""",
        input_variables=["docs", "question"]
    )
    
    try:
        grader_chain = prompt | llm | StrOutputParser()
        grade = grader_chain.invoke({"docs": docs_text, "question": question}).strip().upper()
        if "YES" in grade:
            return {"web_search_needed": False}
        return {"web_search_needed": True}
    except Exception:
        return {"web_search_needed": False}


def conduct_web_search(state: PortfolioState):
    """Performs live web fallback when external data is required."""
    question = state["question"]
    try:
        search_res = web_search_tool.run(question)
    except Exception as e:
        search_res = "Web search is currently unavailable."
        
    existing_docs = state.get("documents", [])
    existing_docs.append(f"[Web Search Result]: {search_res}")
    return {"documents": existing_docs}


def generate_answer(state: PortfolioState):
    """Synthesizes a polished, professional response representing Vivek."""
    question = state["question"]
    docs_text = "\n\n".join(state.get("documents", []))
    route = state.get("route", "")
    
    prompt = PromptTemplate(
        template="""You are the official, professional AI Portfolio Agent for Vivek Kumar Pandit.
Your goal is to provide crisp, well-structured, brief, and 100% factually accurate answers using the Verified Knowledge Context below.

Visitor Question:
{question}

Verified Knowledge Context:
{docs}

Routing Category: {route}

CRITICAL RULES & GUIDELINES:
1. STRICT FACTUAL ACCURACY: Only use facts explicitly stated in the context. Never hallucinate unnamed companies or non-existent roles.
2. EDUCATION: If asked about education or academic background, explicitly mention:
   - B.Tech in Information Technology from KJ Somaiya College of Engineering (K. J. Somaiya), Vidyavihar, Mumbai (Class of 2026)
   - Academic GPA / CGPA: 8.75 / 10
3. WORK EXPERIENCE & INTERNSHIPS:
   - If asked about "work experience": Explain that Vivek is a fresh graduate (Class of 2026) and does not have full-time corporate work experience as of now. However, he has gained extensive practical, production-level industry experience through three rigorous software engineering internships:
     1. **Mehery Soccom Pvt. Ltd.** – Full-Stack Developer Intern (Jan 2026 – Jun 2026)
     2. **Common Wealth** – Software Engineer Intern (Jan 2025 – May 2025)
     3. **MeshCraft** – Frontend Developer Intern (Aug 2024 – Sep 2024)
   - If asked for internship details, list these exact company names, roles, durations, and key architectural contributions.
4. PROJECTS: When discussing projects, highlight key features, architecture (e.g. Medallion architecture for Data Warehouse, WebRTC/Socket.io for SoMo/Mehery, React Native for EducationConnect, Gemini/Next.js for Saveior) and GitHub links.
5. FORMATTING: Use clean GitHub-flavored Markdown with bold headers and bullet points (-). Do NOT use HTML tags (like <br>). Keep the response concise, punchy, and professional.
6. HONESTY: If a question asks for details not present in the verified context, state: "I don't have information about that in my knowledge base. You can view Vivek's full profile on his LinkedIn: https://www.linkedin.com/in/vivek-pandit-368b012a7/"

Response:""",
        input_variables=["question", "docs", "route"]
    )
    
    try:
        response_chain = prompt | llm | StrOutputParser()
        answer = response_chain.invoke({
            "question": question,
            "docs": docs_text,
            "route": route
        })
    except Exception as e:
        answer = "I apologize, but I encountered a temporary issue generating the response. Please feel free to reach out to Vivek directly via [LinkedIn](https://www.linkedin.com/in/vivek-pandit-368b012a7/) or [Email](mailto:vivek.pandit1499@gmail.com)."
    
    return {"generation": answer}


# 5. Routing Decisions (Edges)
def decide_route(state: PortfolioState):
    route = state.get("route", "resume_rag")
    if route == "resume_rag":
        return "retrieve_resume"
    elif route == "web_search":
        return "conduct_web_search"
    return "generate_answer"


def decide_after_grading(state: PortfolioState):
    if state.get("web_search_needed", False):
        return "conduct_web_search"
    return "generate_answer"


# 6. Assemble LangGraph Workflow
workflow = StateGraph(PortfolioState)

workflow.add_node("route_query", route_query)
workflow.add_node("retrieve_resume", retrieve_resume)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("conduct_web_search", conduct_web_search)
workflow.add_node("generate_answer", generate_answer)

workflow.add_edge(START, "route_query")

workflow.add_conditional_edges(
    "route_query",
    decide_route,
    {
        "retrieve_resume": "retrieve_resume",
        "conduct_web_search": "conduct_web_search",
        "generate_answer": "generate_answer"
    }
)

workflow.add_edge("retrieve_resume", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    decide_after_grading,
    {
        "conduct_web_search": "conduct_web_search",
        "generate_answer": "generate_answer"
    }
)

workflow.add_edge("conduct_web_search", "generate_answer")
workflow.add_edge("generate_answer", END)

portfolio_graph = workflow.compile()
