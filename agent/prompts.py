"""Prompt templates for the CSE476 reasoning agent."""

# Default system prompt used when no domain-specific prompt is available
SYSTEM_DEFAULT = "You are a helpful and precise reasoning assistant. Think carefully before answering."

# Domain-specific system prompts
SYSTEM_MATH = (
    "You are an expert mathematics assistant. "
    "Solve the problem step by step and provide only the final numerical answer on the last line."
)

SYSTEM_CODING = (
    "You are an expert Python programmer. "
    "Write clean, correct, self-contained code. "
    "Return only the final answer or the completed function — no extra commentary."
)

SYSTEM_COMMON_SENSE = (
    "You are a knowledgeable assistant with strong common-sense reasoning. "
    "Answer concisely and directly."
)

SYSTEM_PLANNING = (
    "You are a careful planning assistant. "
    "Evaluate the plan step by step and provide a clear final verdict."
)

SYSTEM_FUTURE_PREDICTION = (
    "You are an analytical assistant skilled at reasoning about future events. "
    "Use the evidence provided and give a concise prediction."
)

# User-facing prompt templates (use .format(**kwargs) to fill placeholders)

PROMPT_DIRECT = "{question}"

PROMPT_CHAIN_OF_THOUGHT = (
    "Answer the following question by thinking through it step by step.\n\n"
    "Question: {question}\n\n"
    "Step-by-step reasoning:"
)

PROMPT_SELF_CONSISTENCY = (
    "Answer the following question. "
    "Think carefully and provide your best answer.\n\n"
    "Question: {question}"
)

PROMPT_MATH_SCRATCHPAD = (
    "Solve the following math problem. "
    "Show your work, then write the final answer on its own line prefixed with 'Answer:'.\n\n"
    "Problem: {question}"
)

PROMPT_CODING_TASK = (
    "Complete the following coding task. "
    "Return only the final, working Python code.\n\n"
    "Task: {question}"
)

PROMPT_PLANNING_EVAL = (
    "You are given a plan. Evaluate whether it is correct and feasible.\n\n"
    "Plan:\n{question}\n\n"
    "Is this plan correct? Answer True or False and briefly explain."
)

PROMPT_FUTURE_PREDICTION = (
    "Based on the context below, predict the most likely outcome.\n\n"
    "{question}\n\n"
    "Prediction:"
)
