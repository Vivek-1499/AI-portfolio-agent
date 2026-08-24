import os
from typing import List, TypedDict
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import StateGraph, START, END

# 1. Environment & Model Setup
load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

# 2. Ingest Corpus & Build Vector Store
loader = TextLoader("./corpus.txt", encoding="utf-8")
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
chunks = text_splitter.split_documents(docs)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
vector_store = FAISS.from_documents(chunks, embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

web_search_tool = DuckDuckGoSearchRun()


# 3. Define Graph State
class PortfolioState(TypedDict):
    question: str
    route: str
    documents: List[str]
    web_search_needed: bool
    generation: str


# 4. Graph Nodes
# Look at the user's question and decide which route this question should take
def route_query(state: PortfolioState):
    """Routes inquiry to either resume knowledge base, external web, or direct conversation."""
    question = state["question"]
    
    prompt = PromptTemplate(
        template="""You are an AI router for Vivek Kumar Pandit's portfolio website.
Classify the following question into EXACTLY ONE category:
- 'resume_rag': For questions regarding Vivek's skills, projects, experience, education, contact info, or background.
- 'web_search': For external tech trends, market salaries, external news, or tools not specific to Vivek.
- 'general_chat': For simple greetings (e.g., 'hello', 'who are you', 'how does this work').

Return ONLY the category name.

Inquiry: {question}
Category:""",
        input_variables=["question"]
    )
    
    router_chain = prompt | llm | StrOutputParser()
    decision = router_chain.invoke({"question": question}).strip().lower()
    
    if "resume" in decision or "rag" in decision:
        decision = "resume_rag"
    elif "web" in decision:
        decision = "web_search"
    else:
        decision = "general_chat"
        
    return {"route": decision}

# Get semantic similar context
def retrieve_resume(state: PortfolioState):
    """Retrieves relevant chunks from Vivek's portfolio corpus."""
    question = state["question"]
    retrieved_docs = retriever.invoke(question)
    doc_strings = [doc.page_content for doc in retrieved_docs]
    return {"documents": doc_strings}

# Grade the documents to know to search or use Rag
def grade_documents(state: PortfolioState):
    """Self-RAG Grader: Checks if retrieved resume context actually contains the answer."""
    question = state["question"]
    docs_text = "\n\n".join(state.get("documents", []))
    
    prompt = PromptTemplate(
        template="""You are a strict relevance grader.
Determine if the retrieved portfolio documents contain sufficient information to answer the user's question about Vivek.

Retrieved Context:
{docs}

Question:
{question}

Respond ONLY with 'YES' if the documents are relevant and helpful, or 'NO' if they lack necessary facts.""",
        input_variables=["docs", "question"]
    )
    
    grader_chain = prompt | llm | StrOutputParser()
    grade = grader_chain.invoke({"docs": docs_text, "question": question}).strip().upper()
    
    if "YES" in grade:
        return {"web_search_needed": False}
    return {"web_search_needed": True}


def conduct_web_search(state: PortfolioState):
    """Performs live web fallback when external data is required."""
    question = state["question"]
    search_res = web_search_tool.run(question)
    
    existing_docs = state.get("documents", [])
    existing_docs.append(f"[Web Search Result]: {search_res}")
    return {"documents": existing_docs}


def generate_answer(state: PortfolioState):
    """Synthesizes a polished, professional response representing Vivek."""
    question = state["question"]
    docs = "\n\n".join(state.get("documents", []))
    route = state.get("route", "")
    
    prompt = PromptTemplate(
        template="""You are the strict, professional AI Ambassador for Vivek Kumar Pandit's professional portfolio.
Your ONLY job is to answer visitor questions using EXACTLY the 'Verified Knowledge Context' below. 

Visitor Question:
{question}

Verified Knowledge Context:
{docs}

Routing Context: {route}

CRITICAL INSTRUCTIONS - YOU MUST OBEY THESE RULES:
1. ZERO HALLUCINATION: You are FORBIDDEN from inventing, guessing, or adding any projects, technologies, frameworks, or metrics that are not explicitly written in the Verified Knowledge Context. 
2. NO HTML TAGS: Do not use HTML tags like <br>. 
3. FORMATTING: Use standard Markdown formatting. Prefer bullet points (-) over tables to ensure clean rendering. If you must use a table, format it strictly in standard markdown without HTML.
4. HONESTY: If the user asks about a skill, project, or role not mentioned in the context, explicitly state: "I don't have information about that in my knowledge base. You can view Vivek's full background on his LinkedIn: https://www.linkedin.com/in/vivek-pandit-368b012a7/"

Response:""",
        input_variables=["question", "docs", "route"]
    )
    
    response_chain = prompt | llm | StrOutputParser()
    answer = response_chain.invoke({
        "question": question,
        "docs": docs,
        "route": route
    })
    
    return {"generation": answer}

# 5. Routing Decisions (Edges)

def decide_route(state: PortfolioState):
    route = state["route"]
    if route == "resume_rag":
        return "retrieve_resume"
    elif route == "web_search":
        return "conduct_web_search"
    return "generate_answer"


def decide_after_grading(state: PortfolioState):
    if state["web_search_needed"]:
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