from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
#from langchain.chat_models import init_chat_model

from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0)

#llm = ChatOpenAI(model="gpt-4o-mini",temperature=0)
#llm = init_chat_model("llama3-8b-8192", model_provider="groq")
#llm = init_chat_model("qwen-2.5-32b", model_provider="groq")
#llm = init_chat_model("mistralai/Mixtral-8x7B-Instruct-v0.1", model_provider="together")

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

structured_llm_grader = llm.with_structured_output(GradeDocuments, method="function_calling")

system = """You are a grader assessing relevance of a retrieved document to a user question. \n
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader



