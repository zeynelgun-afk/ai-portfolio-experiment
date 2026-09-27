#!/usr/bin/env python3
"""Check every number in an LLM's output against the numbers it was given.

Why this exists: WEEKLY_INSTRUCTIONS.md says "never write a number without a source",
and round #7 broke exactly that rule — an "~80-90% market share" figure was written
into the NVDA thesis from memory. The instructions themselves prescribe the remedy:
**"If writing a rule down is not enough, the rule gets turned into data."** A prompt is
not a firewall; this module turns that rule into code.

The rule in one sentence: **every number in the output must either appear in the prompt
or be derivable from two numbers in the prompt.** Derivation is deliberately generous,
because the instructions require percentages to be written with their base — "+14.9%
above the 50-day average" is a legitimate calculation that never appears verbatim in the
prompt, so pairwise ratios join the allowed set.

False positives are accepted on purpose: if a number is flagged unfairly, the outcome is
that the claim is LEFT UNCHANGED (the old text stands), not that a fabricated number
gets written. The gate is built to fail in that direction.
"""

import re

# Number formats: 1,082.28 · 1.082,28 · 905.4 · 3.6 · -7 · 941
_THOUSANDS_DOT = re.compile(r"^\d{1,3}(?:\.\d{3})+(?:,\d+)?$")
_THOUSANDS_COMMA = re.compile(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
_NUMBER = re.compile(r"\d[\d.,]*\d|\d")

# Counting and ordinal numbers: "three rounds running", "2 consecutive checks",
# "3 days". Too small to carry a fabricated ratio, so they pass freely.
COUNT_CEILING = 12

# Indicator parameters are terms, not claims: "50d average", "RSI(14)", "20-day
# volume", "200d". The model will write these whether or not they appear in the data
# block, and none of them asserts anything about the market. Catching them would be a
# pure false positive, and rejecting legitimate commentary undermines the gate's own
# purpose.
FREE_TERMS = {14, 20, 50, 200}

# The tolerance is ABSOLUTE only. A relative tolerance was tried and made the gate
# useless: 0.1% of 2026 is 2.03, so a fabricated "2027" slipped through silently.
# An absolute 0.051 is enough to forgive written rounding (3.65 -> "3.6", 905.4 ->
# "905.40") without swallowing the neighbouring integer.
ABSOLUTE_TOLERANCE = 0.051

# Derivation only runs over pairs of the SAME ORDER OF MAGNITUDE. Left unbounded (the
# first attempt), 14 source numbers produced ~2,200 allowed values and the percentage
# space became so dense that round #7's real hallucination ("80-90% market share")
# counted as "derivable" and passed. Comparing a price to a price is meaningful;
# comparing a price to a share count is not.
DERIVATION_RATIO_MIN = 0.1
DERIVATION_RATIO_MAX = 10.0

# Only measurement-sized numbers enter the derivation base. Fragments of dates and
# identifiers (the 9 in 2026-09-30, the 5 in intraday_5m) produced (9/5-1)*100 = 80,
# which is precisely how round #7's "80-90% market share" walked through the gate.
# Integers below this floor already pass as counts, so excluding them from the base
# loses no legitimate number.
DERIVATION_BASE_FLOOR = 12


def _normalize(raw):
    """'1.082,28' -> 1082.28 · '1,082.28' -> 1082.28 · '905.4' -> 905.4"""
    text = raw.strip(".,")
    if not text:
        return None
    if _THOUSANDS_DOT.match(text):
        text = text.replace(".", "").replace(",", ".")
    elif _THOUSANDS_COMMA.match(text):
        text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
        if text.count(".") > 1:  # ambiguous form like 1.082.28 — drop the extras
            text = text.replace(".", "", text.count(".") - 1)
    try:
        return float(text)
    except ValueError:
        return None


def extract_numbers(text):
    """Return the numbers in a text as a list of (raw_text, value) pairs."""
    found = []
    for match in _NUMBER.finditer(text or ""):
        raw = match.group(0)
        value = _normalize(raw)
        if value is not None:
            found.append((raw, value))
    return found


def _written_forms(value):
    """The legitimate ways one number can be written: rounded AND truncated.

    For a condition whose threshold is 941.62 the model may write "above 941" —
    rounding gives 942, truncating gives 941. Both are legitimate; accepting only the
    rounded form closed the gate in the wrong place (a real decision was rejected for
    exactly this reason during testing).
    """
    forms = {value, abs(value)}
    for places in (0, 1, 2):
        for x in (value, abs(value)):
            forms.add(round(x, places) if places else float(round(x)))
            scale = 10 ** places
            forms.add(int(x * scale) / scale)  # truncation
    return forms


def allowed_values(*texts):
    """Numbers from the prompt plus the ratios and differences derivable from them."""
    source = set()
    for text in texts:
        for _, value in extract_numbers(text):
            source.add(value)

    allowed = set(source)
    for value in source:
        allowed.update(_written_forms(value))

    base = [v for v in source if abs(v) > DERIVATION_BASE_FLOOR]
    for a in base:
        for b in base:
            if a == b or not b:
                continue
            if not (DERIVATION_RATIO_MIN <= abs(a / b) <= DERIVATION_RATIO_MAX):
                continue  # different magnitudes: the comparison carries no meaning
            for derived in ((a / b - 1) * 100, a / b, a - b):
                if not (-1e9 < derived < 1e9):
                    continue
                # Derived values get rounding only, NOT truncation. The full set of
                # written forms was tried: it pushed the allowed set to 624 values and
                # let 40% of all two-digit integers through by accident. The
                # instructions already require percentages to carry their base and a
                # decimal ("-3.8%"); a derived percentage written as a bare integer is
                # not the normal case.
                allowed.update({round(derived, 1), round(derived, 2),
                                round(abs(derived), 1), round(abs(derived), 2)})
    return allowed


def _is_allowed(value, allowed):
    if abs(value) <= COUNT_CEILING and float(value).is_integer():
        return True  # counting or ordinal number
    if value in FREE_TERMS:
        return True  # indicator parameter (50d, RSI 14, 20d volume, 200d)
    return any(abs(value - a) <= ABSOLUTE_TOLERANCE for a in allowed)


def unsourced_numbers(output, *sources):
    """Numbers in the output that appear in no source and derive from none.

    Returns [(raw_text, value), ...] — an empty list means clean.
    """
    allowed = allowed_values(*sources)
    unsourced, seen = [], set()
    for raw, value in extract_numbers(output):
        if _is_allowed(value, allowed) or value in seen:
            continue
        seen.add(value)
        unsourced.append((raw, value))
    return unsourced


def correction_prompt(unsourced):
    """The correction the model is given on its second attempt."""
    listed = ", ".join(raw for raw, _ in unsourced)
    return (
        "Your previous answer contained numbers that do NOT appear in the data block "
        f"you were given, and cannot be derived from it either: {listed}.\n"
        "Those are unsourced numbers and the experiment's charter forbids them. Rewrite "
        "the answer: remove those numbers entirely, or replace them with numbers that "
        "DO appear in the data block. If you cannot verify a number, build the sentence "
        "without it — a thesis can be stated without numbers. Return only JSON, in the "
        "same schema as before."
    )
