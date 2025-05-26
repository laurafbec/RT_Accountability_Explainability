from typing import Any, Dict

from graph.state import GraphState
from load_data import retriever
import re

def extract_timestamp(page_content: str) -> float:
    match = re.match(r"^\d+\.\d+", page_content)
    if match:
        return float(match.group(0))
    else:
        return 0.0  # Default if no timestamp is found

def retrieve(state: GraphState) -> Dict[str, Any]:
    print("---RETRIEVE---")
    question = state["question"]
    loop_step = state.get("loop_step", 0)

    documents = retriever.invoke(question)

    sorted_documents = sorted(documents, key=lambda doc: extract_timestamp(doc.page_content))

    history = state.get("history", [])
    history.append({"role": "user", "message": question})

    return {"documents": sorted_documents, "question": question, "history": history, "loop_step":loop_step+1}