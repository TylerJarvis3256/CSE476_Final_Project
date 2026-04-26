from agent import prompts, tools
from agent.llm import build_messages, call_model


def solve(input_text):
    # The assignment says not to refuse future-prediction questions, so the prompt
    # always asks for a concrete boxed prediction.
    prompt_text = prompts.FUTURE_PREDICTION.format(problem=input_text)
    raw_response = call_model(
        build_messages(prompt_text, prompts.SYSTEM_DEFAULT),
        temperature=0.2,
        max_tokens=300,
    )

    boxed = tools.extract_boxed(raw_response)
    if boxed is not None:
        return tools.truncate_answer(rf"\boxed{{{boxed}}}")

    list_like = tools.parse_list_like(raw_response)
    if len(list_like) > 1:
        return tools.truncate_answer(tools.ensure_boxed(str(list_like)))

    final = tools.extract_final_answer(raw_response)
    return tools.truncate_answer(tools.ensure_boxed(final))
