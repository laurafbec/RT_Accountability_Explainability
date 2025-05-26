import csv
import asyncio
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from ragas.metrics import RubricsScore
from ragas.dataset_schema import SingleTurnSample
from dotenv import load_dotenv
import os
from user_criteria import rubrics
import json
from consts import *

from ragas.metrics._aspect_critic import harmfulness

load_dotenv()



# Load the JSON file into a variable
with open(DATASET_FILE, "r", encoding="utf-8") as file:
    dataset = json.load(file)


llm = ChatOpenAI(model="gpt-4o-mini")
#llm = ChatOpenAI(model="gpt-4")
#llm = ChatOpenAI(model="gpt-4o")
evaluator_llm = LangchainLLMWrapper(llm)


async def evaluate_example(example, evaluator_llm, rubrics):
    rubric_results = {}
    for rubric_name, rubric_definitions in rubrics.items():
        scorer = RubricsScore(rubrics=rubric_definitions, llm=evaluator_llm)
        rubric_result = await scorer.single_turn_ascore(
            SingleTurnSample(response=example["response"], reference=example["reference"])
        )
        rubric_results[rubric_name] = rubric_result
    return rubric_results


async def main():
    output_file = f"results/criteria_evaluation_{SCENARIOID}_{RUNID}.csv"

    # Evaluate all examples
    tasks = [evaluate_example(example, evaluator_llm, rubrics) for example in dataset]
    results = await asyncio.gather(*tasks)

    # Get rubric names for column headers dynamically
    rubric_names = list(rubrics.keys())

    # Write results in a single row per example
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write header
        writer.writerow(["SCENARIOID", "RUNID", "ExampleID"] + rubric_names)

        # Write evaluation results
        for idx, rubric_results in enumerate(results):
            example_id = idx + 1
            row = [SCENARIOID, RUNID, example_id] + [rubric_results.get(rubric, "N/A") for rubric in rubric_names]
            writer.writerow(row)


if __name__ == "__main__":
    asyncio.run(main())





