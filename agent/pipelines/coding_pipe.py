from agent import prompts, tools
from agent.llm import build_messages, call_model
from agent.techniques import self_refine


def solve(input_text):
    # Some coding questions include required starter code.
    required_prefix = tools.extract_required_prefix(input_text)

    # First draft: ask for code only.
    prompt_text = prompts.CODING_GEN.format(
        problem=input_text,
        required_prefix=required_prefix or "(none)",
    )
    raw_draft = call_model(
        build_messages(prompt_text, prompts.SYSTEM_DEFAULT),
        temperature=0.1,
        max_tokens=1200,
    )
    code = tools.clean_code_answer(raw_draft, required_prefix=required_prefix)

    # If the first draft looks messy, give the model one repair pass.
    needs_refine = False
    if not code:
        needs_refine = True
    if "```" in raw_draft:
        needs_refine = True
    if required_prefix and not code.startswith(required_prefix.strip()):
        needs_refine = True

    if needs_refine:
        critique = (
            "Return only executable Python code, remove explanation, "
            "and preserve the required prefix exactly."
        )
        refined = self_refine(
            input_text,
            code or raw_draft,
            critique=critique,
            required_prefix=required_prefix,
            max_tokens=1200,
        )
        code = tools.clean_code_answer(refined, required_prefix=required_prefix)

    return tools.truncate_answer(code)
