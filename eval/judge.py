from agent.llm import build_messages, call_model


def judge_prediction(question, expected, predicted, domain):
    # This is a simple LLM-as-a-judge fallback for cases where string matching is too strict.
    prompt_text = f"""
You are a strict grader for a reasoning benchmark.
Reply with only True or False.

Domain: {domain}
Question:
{question}

Expected answer:
{expected}

Predicted answer:
{predicted}

Return True only if the predicted answer should be accepted as correct.
""".strip()

    raw_response = call_model(
        build_messages(
            prompt_text,
            "You are a strict grader. Reply with only True or False.",
        ),
        temperature=0.0,
        max_tokens=10,
    )

    return raw_response.strip().lower().startswith("true")
