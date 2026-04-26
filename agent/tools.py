"""Utility helpers and answer normalizers for the CSE476 reasoning agent.

All functions in this module use only the Python standard library — no external
dependencies are required.
"""

import re
import string
import unicodedata


# ---------------------------------------------------------------------------
# General text utilities
# ---------------------------------------------------------------------------

def normalize_whitespace(text):
    """Collapse any run of whitespace into a single space and strip ends."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def remove_punctuation(text):
    """Remove all punctuation characters from *text*."""
    return text.translate(str.maketrans("", "", string.punctuation))


def normalize_unicode(text):
    """Convert *text* to NFC unicode normal form."""
    return unicodedata.normalize("NFC", text)


def clean_text(text):
    """Apply unicode normalisation, collapse whitespace, and lowercase."""
    if not text:
        return ""
    text = normalize_unicode(text)
    text = normalize_whitespace(text)
    return text.lower()


# ---------------------------------------------------------------------------
# Answer extraction helpers
# ---------------------------------------------------------------------------

def extract_last_line(text):
    """Return the last non-empty line of *text*."""
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def extract_answer_after_prefix(text, prefix="Answer:"):
    """Return the text that follows *prefix* (case-insensitive), or None."""
    pattern = re.compile(re.escape(prefix), re.IGNORECASE)
    match = pattern.search(text or "")
    if match:
        return text[match.end():].strip()
    return None


def extract_first_number(text):
    """Return the first integer or decimal number found in *text*, or None."""
    match = re.search(r"-?\d+(?:\.\d+)?", text or "")
    return match.group() if match else None


def extract_yes_no(text):
    """Return 'yes', 'no', or None by scanning the start of *text*."""
    cleaned = clean_text(text or "")
    if re.match(r"\byes\b", cleaned):
        return "yes"
    if re.match(r"\bno\b", cleaned):
        return "no"
    return None


def extract_true_false(text):
    """Return 'true', 'false', or None from the start of *text*."""
    cleaned = clean_text(text or "")
    if cleaned.startswith("true"):
        return "true"
    if cleaned.startswith("false"):
        return "false"
    return None


# ---------------------------------------------------------------------------
# Math answer normalizers
# ---------------------------------------------------------------------------

def normalize_math_answer(text):
    """Strip whitespace, remove surrounding punctuation, and normalise a math answer.

    Examples
    --------
    >>> normalize_math_answer('  42  ')
    '42'
    >>> normalize_math_answer('$3.14.')
    '3.14'
    """
    if text is None:
        return ""
    text = str(text).strip()
    # Remove common surrounding symbols: $, commas in numbers, trailing periods
    text = text.replace(",", "")
    text = re.sub(r"^\$+|\$+$", "", text)
    text = text.rstrip(".")
    return text.strip()


def parse_numeric(text):
    """Try to convert *text* to float; return None if not possible."""
    try:
        return float(normalize_math_answer(text))
    except (ValueError, TypeError):
        return None


def numbers_are_close(a, b, rel_tol=1e-4):
    """Return True if two numeric strings represent approximately equal values."""
    fa = parse_numeric(a)
    fb = parse_numeric(b)
    if fa is None or fb is None:
        return False
    if fa == fb == 0:
        return True
    return abs(fa - fb) <= rel_tol * max(abs(fa), abs(fb))


# ---------------------------------------------------------------------------
# String matching / scoring helpers
# ---------------------------------------------------------------------------

def normalize_answer(text):
    """Lowercase, strip punctuation and extra whitespace — canonical form for comparison."""
    if not text:
        return ""
    text = clean_text(text)
    text = remove_punctuation(text)
    return normalize_whitespace(text)


def exact_match(prediction, expected):
    """Return True if normalised *prediction* equals normalised *expected*."""
    return normalize_answer(prediction) == normalize_answer(expected)


def contains_match(prediction, expected):
    """Return True if *expected* (normalised) appears somewhere in *prediction* (normalised)."""
    return normalize_answer(expected) in normalize_answer(prediction)


def token_overlap_score(prediction, expected):
    """Return the F1-style token overlap score between prediction and expected."""
    pred_tokens = set(normalize_answer(prediction).split())
    exp_tokens = set(normalize_answer(expected).split())
    if not pred_tokens or not exp_tokens:
        return 0.0
    common = pred_tokens & exp_tokens
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(exp_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ---------------------------------------------------------------------------
# Domain-specific answer checkers
# ---------------------------------------------------------------------------

def check_math(prediction, expected):
    """Return True if prediction and expected represent the same number (with tolerance)."""
    if numbers_are_close(prediction, expected):
        return True
    return exact_match(normalize_math_answer(prediction), normalize_math_answer(expected))


def check_yes_no(prediction, expected):
    """Return True if both prediction and expected resolve to the same yes/no value."""
    pred = extract_yes_no(prediction)
    exp = extract_yes_no(expected)
    if pred is None or exp is None:
        return exact_match(prediction, expected)
    return pred == exp


def check_true_false(prediction, expected):
    """Return True if both prediction and expected resolve to the same true/false value."""
    pred = extract_true_false(prediction)
    exp = extract_true_false(expected)
    if pred is None or exp is None:
        return exact_match(prediction, expected)
    return pred == exp


def check_answer(prediction, expected, domain=None):
    """Dispatch to the appropriate checker for *domain*, falling back to exact match.

    Parameters
    ----------
    prediction : str
        The model's raw output.
    expected : str
        The ground-truth answer.
    domain : str or None
        One of 'math', 'coding', 'planning', 'future_prediction', 'common_sense', or None.

    Returns
    -------
    bool
        True if the prediction should be considered correct.
    """
    if domain == "math":
        return check_math(prediction, expected)
    if domain in ("planning", "future_prediction"):
        tf = check_true_false(prediction, expected)
        if tf is not None:
            return tf
    if domain == "common_sense":
        yn = check_yes_no(prediction, expected)
        if yn is not None:
            return yn
        return exact_match(prediction, expected) or contains_match(prediction, expected)
    # Default: exact match with token-overlap fallback
    if exact_match(prediction, expected):
        return True
    if token_overlap_score(prediction, expected) >= 0.8:
        return True
    return False


# ---------------------------------------------------------------------------
# Misc utilities
# ---------------------------------------------------------------------------

def truncate(text, max_chars=200, suffix="..."):
    """Return *text* truncated to *max_chars*, appending *suffix* if cut."""
    if not text or len(text) <= max_chars:
        return text or ""
    return text[:max_chars].rstrip() + suffix


def safe_strip(value):
    """Return stripped string, or empty string for None / non-string values."""
    if value is None:
        return ""
    return str(value).strip()


def is_empty(value):
    """Return True if *value* is None, empty string, or whitespace-only."""
    return not safe_strip(value)


def dict_get(d, *keys, default=None):
    """Safely get a nested value from a dict using a chain of keys."""
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current
