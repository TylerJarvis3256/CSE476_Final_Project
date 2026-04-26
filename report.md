# CSE476 Reasoning Agent Report

## Overview

This project implements a general-purpose inference-time reasoning agent for five domains: math, coding, common sense, planning, and future prediction. The system routes each question to a domain-specific pipeline and keeps all LLM access on the ASU-hosted API.

## Techniques Implemented

1. Chain-of-Thought: `agent/techniques.py::cot`
2. Self-Consistency: `agent/techniques.py::self_consistency`
3. Program-of-Thought: `agent/techniques.py::program_of_thought`
4. Tree-of-Thoughts: `agent/techniques.py::tree_of_thoughts`
5. Self-Refine: `agent/techniques.py::self_refine`
6. Decomposition: `agent/techniques.py::decomposition`
7. Step-Back Prompting: `agent/techniques.py::step_back`
8. ReAct-style Reasoning: `agent/techniques.py::react_loop`
9. Judge / Verification: `agent/techniques.py::judge`

## Per-Domain Strategy

- Math: combine program-of-thought with self-consistency, then add CoT, ToT, and ReAct candidates, and let the judge select the final answer.
- Coding: generate self-contained Python code, preserve the required prefix from the prompt, and repair malformed outputs with self-refine.
- Common sense: decompose long questions into subquestions, answer them, synthesize, and arbitrate against step-back and direct-answer candidates.
- Planning: summarize action constraints with step-back prompting, generate action-only plans, then repair invalid formatting.
- Future prediction: force a single constrained boxed prediction and repair the output format if needed.

## Efficiency

The per-item LLM client enforces a hard call cap of 15 with a warning at 12. Each domain pipeline is designed to stay below the course limit of 20 calls per item, and `run_agent.py` records per-item call counts to `outputs/calls_log.json`.

## How To Run

Use `run_agent.py` with an input JSON file and output path. Use `eval/evaluate.py` on development data to compute per-domain accuracy and optional LLM-judge scores.

## Limitations

The hidden course grader may use acceptance logic that differs from the local evaluator. The domain router uses heuristics first and only falls back to an LLM classification call when needed, so misclassification remains a possible failure mode on ambiguous items.
