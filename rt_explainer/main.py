from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from pprint import pprint

from graph.graph import app
import re

import json
from evaluation.consts import *


def process_and_get_output(app, inputs):
    for output in app.stream(inputs, config={"configurable": {"thread_id": "2"}}):
        generation = output.get("generation")  # Use get() to avoid KeyError
        if generation:
            return value["generation"]
    return None


def convert_timestamp(timestamp_str):
  """
  Converts a timestamp string (in UNIX format) to a human-readable format.

  Args:
      timestamp_str (str): The timestamp string to convert.

  Returns:
      str: The human-readable timestamp or None if the conversion fails.
  """
  try:
      timestamp = float(timestamp_str)
      readable_timestamp = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
      return readable_timestamp
  except ValueError:
      print(f"Error: Invalid timestamp value: {timestamp_str}")
      return None

# Load the JSON file into a variable
with open(QA_FILE, "r", encoding="utf-8") as file:
    dataset = json.load(file)


output_file = f"evaluation/datasets/dataset_{SCENARIOID}_{RUNID}.json"
for i, example in enumerate(dataset):
    user_input = example["user_input"]
    reference = example["reference"]

    inputs = {"question": user_input}

    for output in app.stream(inputs, config={"configurable": {"thread_id": "2"}}):
        for key, value in output.items():
            pprint(f"Finished running: {key}:")

    # Save to a JSON file
    page_contents = [doc.page_content for doc in value['documents']]
    print(f"Documents content: {page_contents}")
    dataset[i]["retrieved_contexts"] = page_contents
    dataset[i]["response"] = value["generation"]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

    print(f"Dataset saved successfully to {output_file}")

    match = re.findall(r"\d{10,}\.\d+", value["generation"])
    if match:
            for timestamp_str in match:
                readable_timestamp = convert_timestamp(timestamp_str)
                if readable_timestamp:
                    value['generation'] = value['generation'].replace(timestamp_str, readable_timestamp)
                else:
                    print("No timestamps found in the generation text.")
            pprint(value["generation"])  # Print the generation without timestamp conversion
    else:
        pprint(value["generation"])

