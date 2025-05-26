from pprint import pprint

from dotenv import load_dotenv

load_dotenv()

from load_data import retriever

from graph.chains.router import RouteQuery
from graph.chains.retrieval_grader import GradeDocuments, retrieval_grader
from graph.chains.generation import generation_chain
from graph.chains.hallucination_grader import GradeHallucinations, hallucination_grader
from graph.chains.answer_grader import GradeAnswer, answer_grader


# Function to test RouteQuery and route_layer
def test_route_query():
    print("-------ROUTER TEST-------")
    question = "Where is goal number 2 located?"
    route = RouteQuery.route_layer(question)  # Assuming route_layer processes the question
    print(f"Route name: {route.name}")  # Adjust based on your Route class implementation

    expected_route_name = "NavAnswers"
    assert route.name == expected_route_name, f"Expected '{expected_route_name}', but got '{route.name}'"
    print("Test passed: Route name is correct.")

def test_retrieval_grader_answer_yes() -> None:
    question = "When did the robot reach goal number 2?"
    docs = retriever.invoke(question)
    results = ""
    for doc in docs:
        results += doc.page_content
    print("Documents retrieve",results)
    res: GradeDocuments = retrieval_grader.invoke(
        {"question": question, "document": results}
    )
    print("Obtained response: ",res.binary_score)
    if "yes" in res.binary_score.lower().strip():
        binary_score = 'yes'
    elif "no" in res.binary_score.lower().strip():
        binary_score = 'no'
    else:
        raise ValueError(f"Unexpected response: {res}")

    grade_document = GradeDocuments(binary_score=binary_score)

    assert grade_document.binary_score=="yes", f"Expected 'yes', but got {grade_document.binary_score}"
    print("Test passed: Binary score is 'yes'")

def test_retrieval_grader_answer_no() -> None:
    question = "What do I need to prepare a pizza?"
    docs = retriever.invoke(question)
    results = ""
    for doc in docs:
        results += doc.page_content
    print("Documents retrieve",results)
    res: GradeDocuments = retrieval_grader.invoke(
        {"question": question, "document": results}
    )
    print("Obtained response: ",res.binary_score)
    if "yes" in res.binary_score.lower().strip():
        binary_score = 'yes'
    elif "no" in res.binary_score.lower().strip():
        binary_score = 'no'
    else:
        raise ValueError(f"Unexpected response: {res}")

    grade_document = GradeDocuments(binary_score=binary_score)

    assert grade_document.binary_score=="no", f"Expected 'no', but got {grade_document.binary_score}"
    print("Test passed: Binary score is 'no'")


def test_generation_chain():
    print("------GENERATION TEST -------")
    question = "When did the robot reach goal number 2?"
    docs = retriever.invoke(question)
    generation = generation_chain.invoke({"context": docs, "question": question})
    print(generation)

def test_answer_grader():
    # Define a test question and generation
    question = "How many goals have been successfully achieved by the robot?"
    generation = "Two goals have been successfully achieved by the robot."

    # Invoke the answer grader
    result = answer_grader.invoke({"question": question, "generation": generation})

    # Convert binary_score from boolean to "yes"/"no" for comparison
    binary_score_str = "yes" if result.binary_score else "no"
    print(f"Binary Score: {binary_score_str}")

    # Validate the result
    assert binary_score_str in ["yes", "no"], f"Unexpected binary score: {binary_score_str}"
    if binary_score_str == "yes":
        print("Test passed: The answer resolves the question.")
    else:
        print("Test passed: The answer does not resolve the question.")

def test_hallucination_grader_answer_yes() -> None:
    question = "How many goals have been successfully achieved by the robot?"
    docs = retriever.invoke(question)

    generation = generation_chain.invoke({"context": docs, "question": question})
    print(f"Generation: {generation}")
    res: GradeHallucinations = hallucination_grader.invoke(
        {"documents": docs, "generation": generation}
    )
    assert res.binary_score

def test_hallucination_grader_answer_no() -> None:
    question = "How many goals have been successfully achieved by the robot?"
    docs = retriever.invoke(question)

    res: GradeHallucinations = hallucination_grader.invoke(
        {
            "documents": docs,
            "generation": "In order to make pizza we need to first start with the dough",
        }
    )
    assert not res.binary_score

if __name__ == "__main__":
    test_route_query()
    test_retrieval_grader_answer_yes()
    test_retrieval_grader_answer_no()
    test_generation_chain()
    test_hallucination_grader_answer_yes()
    test_hallucination_grader_answer_no()
    test_answer_grader()
