from agent import prompts, tools
from agent.llm import CallBudgetExceeded
from agent.techniques import cot
from agent.techniques import judge
from agent.techniques import program_of_thought
from agent.techniques import react_loop
from agent.techniques import self_consistency
from agent.techniques import tree_of_thoughts


def pot_sampler(question):
    result = program_of_thought(question)
    return str(result.get("answer", "")).strip()


def solve(input_text):
    # Math gets the most complicated pipeline because many of the dev examples
    # look like exact-answer reasoning problems.
    candidates = []

    try:
        # 1. Try program-of-thought several times and vote.
        pot_result = self_consistency(
            input_text,
            sampler=pot_sampler,
            samples=3,
            normalizer=tools.normalize_math_answer,
        )
        pot_answer = str(pot_result.get("answer", "")).strip()
        if pot_answer:
            candidates.append(pot_answer)

        # 2. Also get a regular chain-of-thought style answer.
        cot_raw = cot(
            input_text,
            prompt_template=prompts.COT_MATH_FALLBACK,
            temperature=0.0,
            max_tokens=700,
        )
        cot_answer = tools.extract_boxed(cot_raw)
        if not cot_answer:
            cot_answer = tools.extract_number(cot_raw)
        if not cot_answer:
            cot_answer = tools.extract_final_answer(cot_raw)
        if cot_answer:
            candidates.append(cot_answer)

        # 3. Only spend more calls if the early answers disagree or failed.
        normalized = set()
        for candidate in candidates:
            if candidate:
                normalized.add(tools.normalize_math_answer(candidate))

        if len(normalized) > 1 or not candidates:
            tot_result = tree_of_thoughts(
                input_text,
                branches=3,
                expected_format="the best short final answer to the math problem",
            )
            tot_answer = str(tot_result.get("answer", "")).strip()
            if tot_answer:
                candidates.append(tot_answer)

            react_answer = str(react_loop(input_text, max_steps=2).get("answer", "")).strip()
            if react_answer:
                candidates.append(react_answer)

        # 4. Use the judge prompt to pick the best of the collected candidates.
        final = judge(
            input_text,
            candidates,
            expected_format="a concise final answer for the math problem",
        )
    except CallBudgetExceeded:
        if candidates:
            final = candidates[0]
        else:
            final = ""

    # Clean the answer before returning it.
    clean_final = tools.extract_boxed(final)
    if not clean_final:
        clean_final = tools.extract_number(final)
    if not clean_final:
        clean_final = tools.extract_final_answer(final)

    return tools.truncate_answer(clean_final)
