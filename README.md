# CSE476 Reasoning Agent

General-purpose reasoning agent for the CSE476 final project using the ASU-hosted OpenAI-compatible API.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

The code is already wired with built-in defaults for the ASU endpoint, model, and API key in `agent/llm.py`. You can still override them with environment variables if needed:

- `OPENAI_API_KEY`
- `API_BASE`
- `MODEL_NAME`

## Run

Generate submission-format outputs:

```bash
python run_agent.py --input C:\path\to\cse_476_final_project_test_data.json --output outputs\predictions.json
```

This writes:

- `outputs/predictions.json` in the required submission shape: `[{ "output": "..." }, ...]`
- `outputs/calls_log.json` with per-item LLM call metadata

## Evaluate On Dev Data

Run the local evaluator on labeled development data:

```bash
python -m eval.evaluate outputs\predictions.json C:\path\to\cse476_final_project_dev_data.json --calls-log outputs\calls_log.json
```

Optional LLM-as-judge fallback:

```bash
python -m eval.evaluate outputs\predictions.json C:\path\to\cse476_final_project_dev_data.json --calls-log outputs\calls_log.json --use-judge
```

## Architecture

The project is organized around a router and five domain pipelines:

- `agent/router.py`: domain detection and dispatch
- `agent/pipelines/math_pipe.py`: PoT, self-consistency, CoT fallback, ToT, ReAct, judge
- `agent/pipelines/coding_pipe.py`: code generation plus self-refine formatting repair
- `agent/pipelines/common_sense_pipe.py`: decomposition, step-back, direct answer voting, judge
- `agent/pipelines/planning_pipe.py`: step-back guided plan generation and format repair
- `agent/pipelines/future_prediction_pipe.py`: constrained boxed prediction generation

Shared reasoning primitives live in:

- `agent/techniques.py`
- `agent/prompts.py`
- `agent/tools.py`
- `agent/llm.py`

## Note

This codebase was assembled without running project tests during implementation, per request. Run the commands above when you are ready to validate behavior.
