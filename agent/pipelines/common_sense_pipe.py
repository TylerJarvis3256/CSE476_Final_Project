from agent import prompts, tools
from agent.llm import build_messages, call_model
from agent.techniques import decomposition
from agent.techniques import judge
from agent.techniques import self_consistency
from agent.techniques import step_back


def direct_answer(question):
    prompt_text = prompts.DIRECT_SHORT_ANSWER.format(question=question)
    raw_response = call_model(
        build_messages(prompt_text, prompts.SYSTEM_DEFAULT),
        temperature=0.2,
        max_tokens=160,
    )
    return tools.extract_final_answer(raw_response)


def solve(input_text):
    # Common-sense questions can be short or multi-hop. I use a few lightweight
    # strategies and then let the judge choose one.
    candidates = []

    # Long questions get a slightly larger decomposition.
    if len(input_text) > 500:
        max_parts = 3
    else:
        max_parts = 2

    decomp_result = decomposition(input_text, max_parts=max_parts)
    decomp_answer = str(decomp_result.get("answer", "")).strip()
    if decomp_answer:
        candidates.append(decomp_answer)

    step_result = step_back(input_text)
    step_answer = str(step_result.get("answer", "")).strip()
    if step_answer:
        candidates.append(step_answer)

    direct_result = self_consistency(
        input_text,
        sampler=direct_answer,
        samples=2,
        normalizer=tools.normalize_phrase,
    )
    voted_answer = str(direct_result.get("answer", "")).strip()
    if voted_answer:
        candidates.append(voted_answer)

    final = judge(
        input_text,
        candidates,
        expected_format="the shortest correct answer phrase to the question",
    )
    final = tools.extract_final_answer(final)
    return tools.truncate_answer(final)
