import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# helper functions
def strip_code_fences(text):
    text = (text or "").strip()
    match = re.search(r"```[a-zA-Z0-9_+-]*\s*(.*?)```", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def extract_code_block(text):
    #we assume the code block is formatted
    text = text or ""
    stripped = strip_code_fences(text)
    if stripped != text.strip():
        return stripped
    # If there are no fences, try to find the start of Python code.
    for marker in ("import ", "from ", "def ", "class "):
        index = text.find(marker)
        if index != -1:
            return text[index:].strip()

    return text.strip()


def extract_boxed(text):
    #future-prediction answers often use \boxed{...}, so we need to too
    text = text or ""
    start = text.find(r"\boxed{")
    if start == -1:
        return None
    index = start + len(r"\boxed{")
    depth = 1
    result = []
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(result).strip()
        result.append(char)
        index += 1
    return None


def extract_integer(text):
    text = text or ""
    boxed = extract_boxed(text)
    if boxed:
        match = re.search(r"-?\d+", boxed)
        if match:
            return match.group(0)
    match = re.search(r"(?:final answer|answer)\s*[:=]\s*(-?\d+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    numbers = re.findall(r"-?\d+", text)
    if numbers:
        return numbers[-1]
    return None

#extracting the number from text
def extract_number(text):
    text = text or ""
    boxed = extract_boxed(text)
    if boxed:
        return boxed

    match = re.search(r"(?:final answer|answer)\s*[:=]\s*([^\n]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
    if numbers:
        return numbers[-1]

    return None


def extract_json_list(text):
    #parsing json required response prompts 
    text = strip_code_fences(text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    payload = text[start : end + 1]

    for loader in (json.loads, ast.literal_eval):
        try:
            value = loader(payload)
            if isinstance(value, list):
                return value
        except Exception:
            pass

    return []

#need comparison using regEx
def normalize_phrase(text):
    text = (text or "").strip().lower()
    text = re.sub(r"^answer\s*[:=]\s*", "", text)
    text = re.sub(r"[^\w\s\\\-\[\]\(\),']", " ", text)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

#best output styles
def extract_final_answer(text):
    text = (text or "").strip()
    boxed = extract_boxed(text)
    if boxed:
        return boxed
    match = re.search(
        r"(?:final answer|answer)\s*[:=]\s*(.+)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        first_line = match.group(1).strip().splitlines()[0].strip()
        return first_line.strip("` ")

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)

    if not lines:
        return ""
    return lines[-1].strip("` ")

# Starter code is often provided
def extract_required_prefix(text):
    match = re.search(
        r"starting with:\s*```(?:python)?\s*(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return ""

def clean_code_answer(text, required_prefix=""):
    code = extract_code_block(text)
    clean_lines = []

    for line in code.splitlines():
        clean_lines.append(line.rstrip())

    while clean_lines and not clean_lines[0].strip():
        clean_lines.pop(0)

    code = "\n".join(clean_lines).strip()

    #If the assignment gave a required prefix, try to force it back in.
    if required_prefix and code:
        required_prefix = required_prefix.strip()
        if not code.startswith(required_prefix):
            if code.startswith("def ") and "def " in required_prefix:
                code_lines = code.splitlines()
                rest = "\n".join(code_lines[1:]).strip()
                if rest:
                    code = required_prefix + "\n" + rest
                else:
                    code = required_prefix
            else:
                code = required_prefix + "\n" + code

    return code.strip()

def extract_action_lines(text):
    #Planning outputs should be a series of lines.
    lines = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if line.startswith("(") and line.endswith(")"):
            lines.append(line)
    return lines

def extract_action_names(problem):
    #The planning prompts list actions like "Attack object" or "Feast object..."
    names = []
    for raw_line in (problem or "").splitlines():
        match = re.match(r"\s*([A-Za-z]+)\s+object", raw_line)
        if match:
            name = match.group(1).lower()
            if name not in names:
                names.append(name)
    return names


def validate_action_lines(text, allowed_actions=None):
    bad_lines = []
    allowed = set(allowed_actions or [])
    pattern = re.compile(r"^\(([a-z_]+)(?: [a-z0-9_]+){1,2}\)$")
    lines = extract_action_lines(text)
    for line in lines:
        match = pattern.match(line)
        if not match:
            bad_lines.append(line)
            continue
        if allowed and match.group(1) not in allowed:
            bad_lines.append(line)

    if not lines:
        bad_lines.append("(missing plan)")

    return len(bad_lines) == 0, bad_lines

def normalize_action_plan(text):
    return "\n".join(extract_action_lines(text)).strip()

def ensure_boxed(text):
    text = (text or "").strip()
    if not text:
        return r"\boxed{}"

    boxed = extract_boxed(text)
    if boxed is not None:
        return rf"\boxed{{{boxed}}}"

    return rf"\boxed{{{text}}}"


def parse_list_like(text):
    #used for future-prediction answers
    text = (text or "").strip()
    payload = extract_boxed(text) or text
    payload = strip_code_fences(payload)
    for loader in (json.loads, ast.literal_eval):
        try:
            value = loader(payload)
            if isinstance(value, list):
                return [str(item).strip() for item in value]
        except Exception:
            pass
    if "," in payload:
        parts = []
        for part in payload.split(","):
            part = part.strip()
            if part:
                parts.append(part)
        return parts
    if payload:
        return [payload]
    return []

def normalize_future_answer(text):
    items = parse_list_like(text)
    if items:
        clean_items = []
        for item in items:
            clean_items.append(normalize_phrase(item))
        return " | ".join(clean_items)
    return normalize_phrase(extract_boxed(text) or text)

def normalize_math_answer(text):
    boxed = extract_boxed(text)
    if boxed:
        return normalize_phrase(boxed)

    number = extract_number(text)
    if number:
        return normalize_phrase(number)

    return normalize_phrase(extract_final_answer(text))

def normalize_code(text):
    code = clean_code_answer(text)
    lines = []
    for line in code.splitlines():
        line = line.rstrip()
        if line.strip():
            lines.append(line)
    return "\n".join(lines).strip()


def majority_vote(candidates, normalizer=None):
    #We count normalized answers but keep the original text.
    tally = {}
    first_original = {}

    for candidate in candidates:
        if not candidate:
            continue

        if normalizer is None:
            key = str(candidate).strip()
        else:
            key = normalizer(candidate)

        if not key:
            continue

        tally[key] = tally.get(key, 0) + 1
        if key not in first_original:
            first_original[key] = str(candidate).strip()

    if not tally:
        return "", {}

    winner_key = max(tally, key=lambda key: (tally[key], key))
    return first_original[winner_key], tally


def truncate_answer(text, limit=4900):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def extract_react_parts(text):
    text = text or ""
    thought = ""
    action = ""
    action_input = ""

    thought_match = re.search(r"Thought:\s*(.*)", text)
    action_match = re.search(r"Action:\s*(.*)", text)
    input_match = re.search(r"Action Input:\s*(.*)", text, flags=re.DOTALL)

    if thought_match:
        thought = thought_match.group(1).strip()
    if action_match:
        action = action_match.group(1).strip().lower()
    if input_match:
        action_input = input_match.group(1).strip()

    return thought, action, action_input

def python_exec(code, timeout_s=5):
    #This runs model-generated Python in a temporary folder.
    code = strip_code_fences(code)
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "WINDIR": os.environ.get("WINDIR", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "scratch.py"
        script_path.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                cwd=temp_dir,
                env=safe_env,
            )
        except subprocess.TimeoutExpired as error:
            return {
                "ok": False,
                "stdout": error.stdout or "",
                "stderr": error.stderr or "",
                "value": None,
                "error": "timeout",
            }
        except Exception as error:
            return {
                "ok": False,
                "stdout": "",
                "stderr": "",
                "value": None,
                "error": str(error),
            }

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    # If the script prints ANSWER=..., use that. Otherwise try to find a number.
    answer_match = re.search(r"ANSWER\s*=\s*(.+)", stdout)
    if answer_match:
        value = answer_match.group(1).strip()
    else:
        value = extract_boxed(stdout) or extract_number(stdout)

    return {
        "ok": result.returncode == 0,
        "stdout": stdout,
        "stderr": stderr,
        "value": value,
        "error": None if result.returncode == 0 else f"exit_code={result.returncode}",
    }


if __name__ == "__main__":
    assert strip_code_fences("```python\nprint(1)\n```") == "print(1)"
    assert extract_integer("FINAL ANSWER: 42") == "42"
    assert extract_boxed(r"test \boxed{abc}") == "abc"
    assert extract_json_list('["a", "b"]') == ["a", "b"]
    assert normalize_phrase("The Arthur's Magazine.") == "arthur's magazine"
    assert validate_action_lines("(feast a b)\n(attack c)", ["feast", "attack"])[0]