from agent import prompts, tools
from agent.llm import build_messages, call_model


def ask_llm(prompt_text, temperature=0.0, max_tokens=512, system_prompt=None):
    # I kept one helper here so the rest of the file does not repeat the same
    # call_model(build_messages(...)) code over and over.
    if system_prompt is None:
        system_prompt = prompts.SYSTEM_DEFAULT

    messages = build_messages(prompt_text, system_prompt)
    return call_model(messages, temperature=temperature, max_tokens=max_tokens)


def cot(question, prompt_template=None, temperature=0.0, max_tokens=512):
    # Simple chain-of-thought prompt.
    if prompt_template is None:
        prompt_template = prompts.COT_MATH_FALLBACK

    prompt_text = prompt_template.format(problem=question, question=question)
    return ask_llm(prompt_text, temperature=temperature, max_tokens=max_tokens)


def self_consistency(question, sampler, samples=3, normalizer=None):
    # Ask the model multiple times, then pick the most common normalized answer.
    candidates = []

    for _ in range(samples):
        answer = sampler(question)
        if answer is None:
            continue
        answer = str(answer).strip()
        if answer:
            candidates.append(answer)

    winner, tally = tools.majority_vote(candidates, normalizer=normalizer)
    return {
        "answer": winner,
        "candidates": candidates,
        "tally": tally,
    }


def judge(question, candidates, expected_format="short final answer"):
    # Remove duplicates first so the judge does not compare the same idea twice.
    unique_candidates = []
    for candidate in candidates:
        candidate = str(candidate).strip()
        if candidate and candidate not in unique_candidates:
            unique_candidates.append(candidate)

    if not unique_candidates:
        return ""
    if len(unique_candidates) == 1:
        return unique_candidates[0]

    lines = []
    for index, candidate in enumerate(unique_candidates, start=1):
        lines.append(f"{index}. {candidate}")
    candidate_text = "\n".join(lines)

    prompt_text = prompts.JUDGE.format(
        question=question,
        expected_format=expected_format,
        candidates=candidate_text,
    )
    raw_response = ask_llm(prompt_text, temperature=0.0, max_tokens=30)

    for char in raw_response:
        if char.isdigit():
            choice = int(char) - 1
            if 0 <= choice < len(unique_candidates):
                return unique_candidates[choice]

    # If the judge reply is messy, just use the first candidate.
    return unique_candidates[0]
