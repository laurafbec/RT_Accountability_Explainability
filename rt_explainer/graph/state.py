import operator
from typing import List, TypedDict, Dict
from typing import List


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
        history: list of documents
    """

    question: str
    generation: str
    documents: List[str]
    history: List[Dict[str,str]]
    max_retries: int  # Max number of retries for answer generation
    loop_step: int