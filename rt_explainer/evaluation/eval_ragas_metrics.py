import csv
import asyncio
import os
from ragas import EvaluationDataset
from ragas.evaluation import evaluate
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from ragas.metrics import (
    LLMContextRecall,
    Faithfulness,
    FactualCorrectness,
    SemanticSimilarity,
    LLMContextPrecisionWithoutReference,
    NoiseSensitivity,
    ResponseRelevancy,
    ContextEntityRecall,
    NonLLMStringSimilarity,
    BleuScore,
    RougeScore
)
from ragas.dataset_schema import SingleTurnSample
from dotenv import load_dotenv

load_dotenv()

import json
from consts import *

# Load the JSON file into a variable
with open(DATASET_FILE, "r", encoding="utf-8") as file:
    dataset = json.load(file)

single_turn_samples = [
    SingleTurnSample(response=example["response"], reference=example["reference"]) for example in dataset
]

llm = ChatOpenAI(model="gpt-4o-mini")
#llm = ChatOpenAI(model="gpt-4o")
evaluator_llm = LangchainLLMWrapper(llm)

metrics = [
    LLMContextRecall(),
    FactualCorrectness(),
    Faithfulness(),
    LLMContextPrecisionWithoutReference(),
    NoiseSensitivity(),
    ResponseRelevancy(),
    ContextEntityRecall(),
    SemanticSimilarity(),
    NonLLMStringSimilarity(),
    BleuScore(),
    RougeScore(),
]

output_file = f"results/metrics_evaluation_results_{SCENARIOID}_{RUNID}.csv"

async def evaluate_example(example, metrics, evaluator_llm):
    result = evaluate(
        dataset=EvaluationDataset.from_list([example]),
        metrics=metrics,
        llm=evaluator_llm,
    )
    return result

async def main():
    """Main function to evaluate the dataset."""
    loop = asyncio.get_event_loop()

    # Evaluate the entire dataset
    result = evaluate(
        dataset=EvaluationDataset.from_list(dataset),
        metrics=metrics,
        llm=evaluator_llm,
    )
    print(f"\nOverall evaluation result:\n{result}")
    
    

    # Check if the file  of individual scores exists to write the header only once
    file_exists = os.path.isfile(output_file)

    tasks = [evaluate_example(example, metrics, evaluator_llm) for example in dataset]
    results = await asyncio.gather(*tasks)
    # Print individual example results
    for idx, result in enumerate(results):
        example_id = idx + 1
        print(f"\nExample {idx + 1} Metrics:")
        print(result)
        df = result.to_pandas()  # Convert result to DataFrame
        df['SCENARIOID'] = SCENARIOID
        df['RUNID'] = RUNID
        df['ExampleID'] = example_id

        df = df[['SCENARIOID', 'RUNID', 'ExampleID'] + [col for col in df.columns if col not in ['SCENARIOID', 'RUNID', 'ExampleID']]]

        print(df.head())       

        # Write to CSV
        df.to_csv(output_file, mode='a', header=not file_exists, index=False)
        file_exists = True  # After the first example, the header won't be written again

if __name__ == "__main__":
    asyncio.run(main())
