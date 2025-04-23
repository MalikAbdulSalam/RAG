from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph
from typing import List
import os, requests

# ------------------ Global Variables ------------------
retriever = None
app = None

# ------------------ LLM Setup (GROQ) ------------------
class ChatGroq:
    def __init__(self, groq_api_key, model_name="Gemma2-9b-It", temperature=0.3):
        self.api_key = groq_api_key
        self.model_name = model_name
        self.temperature = temperature

    def invoke(self, messages: List[HumanMessage]):
        user_input = "\n".join([m.content for m in messages if isinstance(m, HumanMessage)])
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": user_input}],
            "temperature": self.temperature
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        return AIMessage(content=response.json()["choices"][0]["message"]["content"])

groq_api_key = os.environ.get("GROQ_API_KEY", "add yout GROQ Api key here")
llm = ChatGroq(groq_api_key=groq_api_key)

# ------------------ LangGraph State Class ------------------
class GraphState(dict):
    input: str
    retrieved_docs: str
    response: str

# ------------------ Functions ------------------

def get_ready_with_pdf(pdf_path):
    global retriever, app

    loader = PyPDFLoader(pdf_path)
    pages = loader.load_and_split()

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(pages, embedding_model)
    retriever = vectorstore.as_retriever()

    def retrieve_node(state: GraphState) -> GraphState:
        query = state["input"]
        docs = retriever.invoke(query)
        return {"retrieved_docs": "\n\n".join(doc.page_content for doc in docs)}

    def generate_node(state: GraphState) -> GraphState:
        query = state["input"]
        docs = state["retrieved_docs"]
        messages = [HumanMessage(content=f"Use the following context to answer:\n{docs}\n\nQuestion: {query}")]
        answer = llm.invoke(messages)
        return {"response": answer.content}

    workflow = StateGraph(GraphState)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.set_finish_point("generate")

    app = workflow.compile()


def query_function(query: str) -> str:
    global app
    if app is None:
        raise ValueError("Call get_ready_with_pdf() before querying.")
    final_state = app.invoke({"input": query})
    return final_state["response"]
