#!/usr/bin/env python3
"""
Generate a placeholder answer file that matches the expected auto-grader format.

Replace the placeholder logic inside `build_answers()` with your own agent loop
before submitting so the ``output`` fields contain your real predictions.

Reads the input questions from cse_476_final_project_test_data.json and writes
an answers JSON file where each entry contains a string under the "output" key.
"""

import json
from pathlib import Path

from agent.router import route_item


INPUT_PATH = Path("cse_476_final_project_test_data.json")
if not INPUT_PATH.exists():
    INPUT_PATH = Path("data/cse_476_final_project_test_data.json")

OUTPUT_PATH = Path("cse_476_final_project_answers.json")


def load_questions(path):
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if type(data) != list:
        raise ValueError("Input file must contain a list of question objects.")
    return data


def build_answers(questions):
    answers = []
    for question in questions:
        #this calls the real agent for each question
        final_answer = route_item(question)
        if final_answer is None:
            final_answer = ""
        answers.append({"output": str(final_answer)})
    return answers


def validate_results(questions, answers):
    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers."
        )

    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if type(answer["output"]) != str:
            raise TypeError(
                f"Answer at index {idx} has non-string output: {type(answer['output'])}"
            )
        if len(answer["output"]) >= 5000:
            raise ValueError(
                f"Answer at index {idx} exceeds 5000 characters "
                f"({len(answer['output'])} chars). Please make sure your answer does not include any intermediate results."
            )


def main():
    questions = load_questions(INPUT_PATH)
    answers = build_answers(questions)

    with OUTPUT_PATH.open("w", encoding="utf-8") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)

    with OUTPUT_PATH.open("r", encoding="utf-8") as fp:
        saved_answers = json.load(fp)

    validate_results(questions, saved_answers)
    print(
        f"Wrote {len(answers)} answers to {OUTPUT_PATH} "
        "and validated format successfully."
    )


if __name__ == "__main__":
    main()