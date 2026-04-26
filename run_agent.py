import argparse
import json
from pathlib import Path

from agent import prompts, tools
from agent.llm import CallBudgetExceeded
from agent.llm import build_messages
from agent.llm import call_model
from agent.llm import get_call_count
from agent.llm import reset_call_count
from agent.router import route_item


def load_items(path):
    # The input file should be a list of question objects.
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError("input file must contain a JSON list")

    items = []
    for item in data:
        if isinstance(item, dict):
            items.append(item)
        else:
            items.append({"input": str(item)})
    return items


def fallback_answer(question):
    # If a pipeline fails, at least try one direct answer instead of returning nothing.
    prompt_text = prompts.DIRECT_SHORT_ANSWER.format(question=question)
    messages = build_messages(prompt_text, prompts.SYSTEM_DEFAULT)
    raw_response = call_model(messages, temperature=0.0, max_tokens=160)
    return tools.extract_final_answer(raw_response)


def solve_items(items, progress_every):
    answers = []
    calls_log = []

    for index, item in enumerate(items, start=1):
        question = item.get("input", "")
        domain_hint = item.get("domain")
        error = ""

        # The call counter is reset for each question because the limit is per item.
        reset_call_count()

        try:
            answer = route_item(item)
        except CallBudgetExceeded as exc:
            answer = ""
            error = str(exc)
        except Exception as exc:
            error = str(exc)
            try:
                answer = fallback_answer(question)
            except Exception:
                answer = ""

        answers.append({"output": tools.truncate_answer(answer)})
        calls_log.append(
            {
                "index": index,
                "domain_hint": domain_hint,
                "calls": get_call_count(),
                "error": error,
            }
        )

        if progress_every and index % progress_every == 0:
            print(f"[progress] solved {index}/{len(items)} items")

    return answers, calls_log


def main():
    parser = argparse.ArgumentParser(description="Run the CSE476 reasoning agent.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file.")
    parser.add_argument("--output", required=True, help="Path to the output JSON file.")
    parser.add_argument(
        "--calls-log",
        default="outputs/calls_log.json",
        help="Where to write per-item call metadata.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50,
        help="Print progress every N items.",
    )
    args = parser.parse_args()

    items = load_items(args.input)
    answers, calls_log = solve_items(items, args.progress_every)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(answers, handle, ensure_ascii=False, indent=2)

    calls_log_path = Path(args.calls_log)
    calls_log_path.parent.mkdir(parents=True, exist_ok=True)
    with calls_log_path.open("w", encoding="utf-8") as handle:
        json.dump(calls_log, handle, ensure_ascii=False, indent=2)

    print(f"wrote {len(answers)} answers to {output_path}")
    print(f"wrote call metadata to {calls_log_path}")


if __name__ == "__main__":
    main()
