import argparse
import json
from pathlib import Path

from agent import tools
from eval.judge import judge_prediction


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def prediction_text(item):
    # Support either {"output": "..."} or {"prediction": "..."} style rows.
    if isinstance(item, dict):
        if "output" in item:
            return str(item["output"])
        if "prediction" in item:
            return str(item["prediction"])
    return str(item)


def strict_match(domain, expected, predicted):
    # Each domain has slightly different formatting, so normalize accordingly.
    if domain == "math":
        return tools.normalize_math_answer(expected) == tools.normalize_math_answer(predicted)
    if domain == "coding":
        return tools.normalize_code(expected) == tools.normalize_code(predicted)
    if domain == "planning":
        return tools.normalize_action_plan(expected) == tools.normalize_action_plan(predicted)
    if domain == "future_prediction":
        return tools.normalize_future_answer(expected) == tools.normalize_future_answer(predicted)
    return tools.normalize_phrase(expected) == tools.normalize_phrase(predicted)


def average_calls(path):
    if not path:
        return None

    path = Path(path)
    if not path.exists():
        return None

    payload = load_json(path)
    if not isinstance(payload, list) or not payload:
        return None

    calls = []
    for item in payload:
        if isinstance(item, dict):
            calls.append(int(item.get("calls", 0)))

    if not calls:
        return None

    return sum(calls) / len(calls)


def evaluate(predictions_path, truth_path, calls_log_path=None, use_judge=False):
    predictions = load_json(predictions_path)
    truth = load_json(truth_path)

    if len(predictions) != len(truth):
        raise ValueError(
            f"mismatched lengths: {len(predictions)} predictions vs {len(truth)} truth rows"
        )

    totals = {}
    correct = {}

    for expected_item, predicted_item in zip(truth, predictions):
        domain = expected_item.get("domain", "common_sense")
        expected = str(expected_item.get("output", ""))
        predicted = prediction_text(predicted_item)

        is_correct = strict_match(domain, expected, predicted)

        # Optional slower fallback: ask the LLM judge if strict matching says false.
        if not is_correct and use_judge:
            is_correct = judge_prediction(
                question=str(expected_item.get("input", "")),
                expected=expected,
                predicted=predicted,
                domain=domain,
            )

        totals[domain] = totals.get(domain, 0) + 1
        correct[domain] = correct.get(domain, 0) + int(is_correct)

    total_items = sum(totals.values())
    total_correct = sum(correct.values())

    print("Per-domain accuracy")
    for domain in sorted(totals):
        score = correct.get(domain, 0)
        total = totals[domain]
        accuracy = score / total if total else 0.0
        print(f"{domain}: {score}/{total} ({accuracy:.2%})")

    overall = total_correct / total_items if total_items else 0.0
    print(f"overall: {total_correct}/{total_items} ({overall:.2%})")

    avg_calls = average_calls(calls_log_path)
    if avg_calls is not None:
        print(f"avg calls/item: {avg_calls:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate CSE476 agent predictions.")
    parser.add_argument("predictions", help="Path to the predictions JSON file.")
    parser.add_argument("truth", help="Path to the labeled dev data JSON file.")
    parser.add_argument("--calls-log", help="Optional path to the call log JSON file.")
    parser.add_argument(
        "--use-judge",
        action="store_true",
        help="Use the ASU model as a fallback grader when strict match fails.",
    )
    args = parser.parse_args()

    evaluate(
        args.predictions,
        args.truth,
        calls_log_path=args.calls_log,
        use_judge=args.use_judge,
    )


if __name__ == "__main__":
    main()
