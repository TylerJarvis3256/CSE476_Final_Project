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


def program_of_thought(question, max_tokens=700):
    # Ask the model to write Python code, then run that code.
    prompt_text = prompts.POT_MATH.format(problem=question)
    raw_response = ask_llm(prompt_text, temperature=0.2, max_tokens=max_tokens)
    code = tools.extract_code_block(raw_response)
    execution = tools.python_exec(code)

    answer = ""
    if execution["value"]:
        answer = str(execution["value"]).strip()

    return {
        "answer": answer,
        "raw": raw_response,
        "code": code,
        "execution": execution,
    }


def self_refine(
    question,
    draft,
    critique,
    prompt_template=prompts.CODING_REFINE,
    required_prefix="",
    max_tokens=900,
):
    # Give the model its own rough draft and ask it to repair it.
    prompt_text = prompt_template.format(
        problem=question,
        draft=draft,
        critique=critique,
        required_prefix=required_prefix,
    )
    return ask_llm(prompt_text, temperature=0.1, max_tokens=max_tokens)


def decomposition(question, max_parts=3):
    # Break a big question into smaller questions, solve those, then combine them.
    prompt_text = prompts.DECOMPOSE.format(question=question, max_parts=max_parts)
    raw_subquestions = ask_llm(prompt_text, temperature=0.0, max_tokens=400)
    parsed_subquestions = tools.extract_json_list(raw_subquestions)

    subquestions = []
    for item in parsed_subquestions[:max_parts]:
        text = str(item).strip()
        if text:
            subquestions.append(text)

    subanswers = []
    for subquestion in subquestions:
        answer_prompt = prompts.SUBQ_ANSWER.format(
            question=question,
            subquestion=subquestion,
        )
        raw_answer = ask_llm(answer_prompt, temperature=0.0, max_tokens=200)
        subanswers.append(
            {
                "question": subquestion,
                "answer": tools.extract_final_answer(raw_answer),
            }
        )

    lines = []
    for item in subanswers:
        lines.append(f"- {item['question']}: {item['answer']}")
    synthesis_text = "\n".join(lines)

    final_prompt = prompts.SYNTHESIS.format(
        question=question,
        subanswers=synthesis_text,
    )
    raw_final = ask_llm(final_prompt, temperature=0.0, max_tokens=250)

    return {
        "answer": tools.extract_final_answer(raw_final),
        "subquestions": subquestions,
        "subanswers": subanswers,
        "raw_subquestions": raw_subquestions,
    }


def step_back(question):
    # This asks for general principles first, then the answer.
    prompt_text = prompts.STEP_BACK.format(question=question)
    raw_response = ask_llm(prompt_text, temperature=0.0, max_tokens=350)

    answer = tools.extract_final_answer(raw_response)
    lower_text = raw_response.lower()
    marker_index = lower_text.find("final answer:")

    if marker_index == -1:
        principles = raw_response.strip()
    else:
        principles = raw_response[:marker_index].strip()

    return {
        "answer": answer,
        "principles": principles,
        "raw": raw_response,
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
