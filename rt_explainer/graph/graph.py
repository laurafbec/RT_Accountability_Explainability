from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from graph.chains.answer_grader import answer_grader
from graph.chains.hallucination_grader import hallucination_grader
from graph.consts import GENERATE, GRADE_DOCUMENTS, RETRIEVE, TRANSFORM_QUERY
from graph.nodes.retrieve import retrieve
from graph.nodes.grade_documents import grade_documents
from graph.nodes.generate import generate
from graph.nodes.transform_query import transform_query
from graph.state import GraphState
from langgraph.graph import END, START

from langgraph.checkpoint.memory import MemorySaver

import re

load_dotenv()
#memory = SqliteSaver.from_conn_string(":memory:")
memory = MemorySaver()


def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")

    filtered_documents = state["documents"]
    max_retries = state.get("max_retries", 1)
    #print(f"---- Loop step-----:\n{state['loop_step']}")

    if not filtered_documents and state["loop_step"] <= max_retries:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_grounded_in_documents_and_question(state: GraphState) -> str:
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    history = state["history"]

    # Use history in hallucination grading
    conversation_history = "\n".join([msg["message"] for msg in history[-8:-2:]])
    print(f"---- Conversation History-----:\n{conversation_history}")

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation, "history": conversation_history}
    )

    if hallucination_grade := score.binary_score:
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation, "history": conversation_history})
        if answer_grade := score.binary_score:
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"



workflow = StateGraph(GraphState)
# Define the nodes
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node(GENERATE, generate)
workflow.add_node(TRANSFORM_QUERY, transform_query)
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)

# Build graph
workflow.add_edge(START, RETRIEVE)
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    {
        TRANSFORM_QUERY: TRANSFORM_QUERY,
        GENERATE: GENERATE,
    },
)
workflow.add_edge(TRANSFORM_QUERY, RETRIEVE)
workflow.add_conditional_edges(
    GENERATE,
    grade_generation_grounded_in_documents_and_question,
    {
        "not supported": GENERATE,
        "useful": END,
        "not useful": TRANSFORM_QUERY
    },
)


app = workflow.compile(checkpointer=memory)

app.get_graph().draw_mermaid_png(output_file_path="graph.png")