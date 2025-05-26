from typing import Any, Dict

from graph.chains.generation import generation_chain
from graph.state import GraphState


def generate(state: GraphState) -> Dict[str, Any]:
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    history = state.get("history", [])

    generation = generation_chain.invoke({"context": documents, "question": question, "history": history})

    history.append({"role": "assistant", "message": generation})

    return {"documents": documents, "question": question, "generation": generation, "history": history, "loop_step": 0}