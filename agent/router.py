from agent import prompts
from agent.llm import build_messages, call_model
from agent.pipelines import coding_pipe
from agent.pipelines import common_sense_pipe
from agent.pipelines import future_prediction_pipe
from agent.pipelines import math_pipe
from agent.pipelines import planning_pipe

# One place that connects each domain name to its pipeline function.
PIPELINES = {
    "math": math_pipe.solve,
    "coding": coding_pipe.solve,
    "common_sense": common_sense_pipe.solve,
    "planning": planning_pipe.solve,
    "future_prediction": future_prediction_pipe.solve,
}


def heuristic_domain(question):
    # Before paying for another model call, try simple keyword rules first.
    text = question or ""
    lowered = text.lower()
    escaped = text.encode("unicode_escape").decode("ascii")

    if "[plan]" in lowered or "my plan is as follows" in lowered:
        return "planning"
    if "predict future events" in lowered or "do not refuse to make a prediction" in lowered:
        return "future_prediction"
    if "\\u8bf7\\u9884\\u6d4b" in escaped or "\\u89c6\\u9891\\u53f7" in escaped:
        return "future_prediction"
    if "write self-contained code" in lowered or "def task_func" in lowered:
        return "coding"
    if "```" in text and "import " in lowered and "def " in lowered:
        return "coding"
    if "$" in text or "\\sqrt" in text or "\\frac" in text:
        return "math"
    if "solve for" in lowered or "find the area" in lowered or "equation" in lowered:
        return "math"
    if "commission" in lowered and "calculate" in lowered:
        return "math"
    return None


def classify_domain(question):
    # Use rules first. If that fails, ask the model to classify the prompt.
    guessed = heuristic_domain(question)
    if guessed is not None:
        return guessed

    prompt_text = prompts.DOMAIN_CLASSIFIER.format(question=question)
    messages = build_messages(prompt_text, prompts.SYSTEM_DEFAULT)
    raw_response = call_model(messages, temperature=0.0, max_tokens=20)

    label = raw_response.strip().lower().replace("-", "_")
    if label in PIPELINES:
        return label

    # Common sense is the safest default bucket if classification is unclear.
    return "common_sense"


def route_item(item):
    question = item.get("input", "")
    domain = item.get("domain")

    if not domain:
        domain = classify_domain(question)

    solver = PIPELINES.get(domain, common_sense_pipe.solve)
    return solver(question)
