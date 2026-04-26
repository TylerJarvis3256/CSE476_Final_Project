from agent import prompts, tools
from agent.llm import build_messages, call_model
from agent.techniques import step_back


def solve(input_text):
    # The planning tasks list a set of allowed actions and want a plan only.
    allowed_actions = tools.extract_action_names(input_text)

    # Step-back helps summarize the rules before plan generation.
    step_result = step_back(input_text)
    summary = step_result.get("principles", "")
    if not summary:
        summary = "Focus on preconditions and effects."

    plan_prompt = prompts.PLANNING.format(
        problem=input_text,
        context=summary,
    )
    raw_plan = call_model(
        build_messages(plan_prompt, prompts.SYSTEM_DEFAULT),
        temperature=0.1,
        max_tokens=900,
    )

    plan = tools.normalize_action_plan(raw_plan)
    valid, bad_lines = tools.validate_action_lines(plan or raw_plan, allowed_actions)

    # If the action format is bad, run one cleanup pass.
    if not valid:
        refine_prompt = prompts.PLANNING_REFINE.format(
            allowed_actions=", ".join(allowed_actions) or "use action names from the problem",
            bad_lines=", ".join(bad_lines),
            problem=input_text,
            draft=raw_plan,
        )
        refined = call_model(
            build_messages(refine_prompt, prompts.SYSTEM_DEFAULT),
            temperature=0.0,
            max_tokens=900,
        )
        plan = tools.normalize_action_plan(refined)

    return tools.truncate_answer(plan)
