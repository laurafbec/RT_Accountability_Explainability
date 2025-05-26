import json
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.evaluation.qa import QAEvalChain
from langchain.evaluation import load_evaluator
from consts import *
import csv


criteria = {
    "correctness": """
        Score 1: The explanation is correct (I disagree strongly).
        Score 2: The explanation is correct (I disagree somewhat).
        Score 3: The explanation is correct (I'm neutral about it).
        Score 4: The explanation is satisfactory (I agree somewhat).
        Score 5: The explanation is satisfactory (I agree strongly).
        """
}


# Load the JSON file into a variable
with open(DATASET_FILE, "r", encoding="utf-8") as file:
    dataset = json.load(file)

eval_examples = [
    {"query": item["user_input"], "answer": item["reference"]}
    for item in dataset
]

predictions = [
    {"result": item["response"]}
    for item in dataset
]

output_file = f"results/correctness_evaluation_{SCENARIOID}_{RUNID}.csv"


llm = ChatOpenAI(model="gpt-4o-mini", request_timeout=120)
#llm = ChatOpenAI(model="gpt-4", request_timeout=120)
eval_chain = QAEvalChain.from_llm(llm)


#predictions.append({"result": value["generation"]})
graded_output = eval_chain.evaluate(eval_examples, predictions)
#print(f"Graded Output for question {i+1}: {graded_output}")
evaluator = load_evaluator("labeled_score_string", criteria=criteria, llm=llm, normalize_by=5)

# Write results in a single row per example
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["SCENARIOID", "RUNID", "ExampleID", "predicted_grade", "reasoning", "score"])

    #for i, value in enumerate(graded_output):
    #    print(f"Element {i}: {value}")

    for i, eg in enumerate(eval_examples):
        print(f"Example {i}:")
        print("Question: " + eval_examples[i]['query'])
        print("Real Answer: " + eval_examples[i]['answer'])
        print("Predicted Answer: " + predictions[i]['result'])
        print("Predicted Grade: " + graded_output[i]['results'])
        print()
        print("----------------------------------------")
        eval_result = evaluator.evaluate_strings(prediction=predictions[i]['result'], reference=eval_examples[i]['answer'], input=eval_examples[i]['query'])
        print(eval_result)
        print("----------------------------------------")
        #print(eval_result['reasoning'].split('.'))
        # Write header
        row = [SCENARIOID, RUNID, i, graded_output[i]['results'], eval_result['reasoning'],  eval_result['score']]
        writer.writerow(row)



