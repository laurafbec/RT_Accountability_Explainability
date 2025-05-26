from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import AspectCritic
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
import json
import csv
from consts import *

from dotenv import load_dotenv

load_dotenv()


sample = SingleTurnSample(
    user_input="Where is the Eiffel Tower located?",
    response="The Eiffel Tower is located in Paris.",
)

# Load the JSON file into a variable
with open(DATASET_FILE, "r", encoding="utf-8") as file:
    dataset = json.load(file)

#llm = ChatOpenAI(model="gpt-4o-mini")
llm = ChatOpenAI(model="gpt-4o")
#llm = ChatOpenAI(model="gpt-4")


evaluator_llm = LangchainLLMWrapper(llm)

scorer = AspectCritic(  # Correct class name
    name="correctness",
    definition="Is the response factually similar to the reference?",
    llm=evaluator_llm
)
output_file = f"results/correctness_evaluation_ragas_{SCENARIOID}_{RUNID}.csv"
samples = []
for example in dataset:
    sample = SingleTurnSample(user_input = example["user_input"], 
        response = example["response"], 
        reference = example["reference"], 
        retrieved_contexts = example["retrieved_contexts"]
        )
    samples.append(sample)

result = evaluate(dataset=EvaluationDataset(samples), metrics=[scorer])
print(result)
print(result.traces[0]["correctness"])

####gpt-4o-mini
# Write results in a single row per example
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Write header
    writer.writerow(["SCENARIOID", "RUNID", "ExampleID", "Reason", "Verdict"])
    for i, trace in enumerate(result.traces):
        print(f"Reason {i}: {trace['correctness']['single_turn_aspect_critic_prompt']['output'].reason}")
        print(f"Verdict {i}: {trace['correctness']['single_turn_aspect_critic_prompt']['output'].verdict}")
        reason = trace['correctness']['single_turn_aspect_critic_prompt']['output'].reason
        verdict = trace['correctness']['single_turn_aspect_critic_prompt']['output'].verdict
        row = [SCENARIOID, RUNID, i, reason, verdict]
        writer.writerow(row)


#print(result.traces[0]["correctness"])
#print(result.traces[1]["correctness"])

#result.upload()

