SYSTEM_DEFAULT = (
    "You are a careful reasoning agent. Think carefully, follow instructions exactly, "
    "and keep the final answer concise."
)

DOMAIN_CLASSIFIER = """
Classify the task into exactly one label from this set:
math
coding
common_sense
planning
future_prediction

Reply with only the label.

Question:
{question}
""".strip()

POT_MATH = """
Solve the math problem by writing runnable Python that computes the answer.
Return only Python code.
The code should print one line in the exact format:
ANSWER=<final_answer>

Problem:
{problem}
""".strip()

COT_MATH_FALLBACK = """
Solve the math problem carefully.
Show concise reasoning and end with a final line in this exact format:
FINAL ANSWER: <answer>

Problem:
{problem}
""".strip()

CODING_GEN = """
Write only the final Python code requested by the task.
Do not include explanation or markdown fences.
If a required code prefix is given, preserve it exactly at the top.

Problem:
{problem}

Required prefix:
{required_prefix}
""".strip()

CODING_REFINE = """
Repair the draft code so it satisfies the task exactly.
Return only Python code with no explanation or markdown fences.
Keep the required prefix exactly as written when one is provided.

Problem:
{problem}

Required prefix:
{required_prefix}

Draft code:
{draft}

Critique:
{critique}
""".strip()

DECOMPOSE = """
Break the question into at most {max_parts} short subquestions that would help solve it.
Return only a JSON array of strings.

Question:
{question}
""".strip()

SUBQ_ANSWER = """
Answer the subquestion using the original question as context.
Reply briefly with only the answer phrase.

Original question:
{question}

Subquestion:
{subquestion}
""".strip()

SYNTHESIS = """
Use the original question and the subanswers to produce the final answer.
Reply with only the final answer and no explanation.

Original question:
{question}

Subanswers:
{subanswers}
""".strip()

DIRECT_SHORT_ANSWER = """
Answer the question directly.
Reply with only the final answer and no explanation.

Question:
{question}
""".strip()

STEP_BACK = """
First state the key principles or facts that matter for this task.
Then give the final answer on a separate line in this exact format:
FINAL ANSWER: <answer>

Question:
{question}
""".strip()

PLANNING = """
Create a valid plan that satisfies the goal.
Return only action lines in the format:
(action arg1)
or
(action arg1 arg2)

Do not include bullets, numbering, or explanation.

Helpful summary:
{context}

Planning problem:
{problem}
""".strip()

PLANNING_REFINE = """
Rewrite the plan so every line is a valid action line and nothing else.
Allowed actions: {allowed_actions}
Bad lines to fix: {bad_lines}

Return only action lines in one of these formats:
(action arg1)
(action arg1 arg2)

Problem:
{problem}

Draft:
{draft}
""".strip()

REACT_MATH = """
Solve the problem with a short ReAct loop.
Allowed actions: python, finish

Reply in exactly this format:
Thought: <brief thought>
Action: <python or finish>
Action Input: <python code if Action is python, otherwise the final answer>

Current scratchpad:
{scratchpad}

Problem:
{problem}
""".strip()

FUTURE_PREDICTION = """
Make the most plausible prediction based on the task wording.
Do not refuse. Do not explain uncertainty.
Your final answer must be a single boxed prediction in this exact format:
\\boxed{{YOUR_PREDICTION}}

Task:
{problem}
""".strip()

TOT_GENERATE = """
Generate {branches} distinct candidate answers for the problem.
Return only a JSON array where each item is an object with keys:
"idea" and "answer"

Problem:
{problem}
""".strip()

JUDGE = """
Choose the best candidate answer for the question.
Prefer answers that are correct, concise, and follow the required format.
Reply with only the candidate number.

Question:
{question}

Expected format:
{expected_format}

Candidates:
{candidates}
""".strip()