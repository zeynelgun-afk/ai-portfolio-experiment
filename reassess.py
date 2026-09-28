#!/usr/bin/env python3
"""Event-driven reassessment — the layer that rewrites the commentary.

detector.py answers only one question, deterministically: "did the meaning change?"
This script puts the changed meaning into words:

  code 10 (claim)  -> only the affected claim is rewritten, by the fast model.
                      Input: the old claim + the triggering data + the time. Output:
                      {text, status: valid|weakened|invalid}
  code 20 (thesis) -> the position's WHOLE thesis is re-evaluated by the deep model and
                      an executable decision is produced (state/pending_decision.json).
                      This script does NOT execute it — execution lives in
                      execute_trade.py, behind deterministic validation.

Budget: MAX_LLM_CALLS_PER_WEEK (default 60) caps weekly calls. Once exceeded only
code-20 calls are made — a thesis-level trigger means an entire thesis is collapsing and
is not sacrificed to a budget.

If the model's JSON cannot be parsed, or it insists on writing numbers it was never
given, the claim is LEFT UNCHANGED and merely marked `unassessed`. Rewriting a thesis
from a half-understood answer is worse than stale commentary.

Usage:
    python reassess.py --code 10
    python reassess.py --code 20
    python reassess.py --full-review      # every claim, fast model
    python reassess.py --code 10 --dry-run  # no LLM calls; prints the prompts
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import number_audit
from prompt_policy import policy
from prompt_adapt import record_result

BASE = os.path.dirname(os.path.abspath(__file__))
THESES_PATH = os.path.join(BASE, "theses.json")
PORTFOLIO_PATH = os.path.join(BASE, "portfolio.json")

# The endpoint is not hardcoded: during an OpenRouter outage, pointing LLM_BASE_URL at
# another OpenAI-compatible endpoint should not require a code change.
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
API_PATH = "/chat/completions"
# Model ids verified against OpenRouter's live catalogue and exercised with a real call
# before being set as defaults — not taken from memory. Opus 5.5 is both newer and cheaper
# than Opus 5 ($4/$20 vs $5/$25 per 1M) at the same 1M context, so the deep tier uses it.
DEFAULT_FAST_MODEL = "anthropic/claude-haiku-4.5"
DEFAULT_DEEP_MODEL = "anthropic/claude-opus-5.5"
DEFAULT_BUDGET = 60
REQUEST_TIMEOUT = 120

# A transient failure or a malformed answer does not deserve giving up on the first try.
MAX_ATTEMPTS = 3
BACKOFF_BASE = 2.0  # seconds; doubles each attempt
SLEEP = time.sleep  # tests replace this to disable real waiting

VALID_STATUSES = {"valid", "weakened", "invalid"}
VALID_ACTIONS = {"HOLD", "BUY", "SELL", "TRIM"}


def env(name, default=""):
    """Every env read is stripped — Actions secrets can carry a trailing newline."""
    return (os.environ.get(name) or default).strip()


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%MZ")


def read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError) as error:
        print(f"WARNING: could not read {os.path.basename(path)} ({error})")
        return default


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


# ---------------------------------------------------------------------- the budget


def week_label(moment):
    year, week, _ = moment.isocalendar()
    return f"{year}-W{week:02d}"


def budget_state(counter_path, moment):
    counter = read_json(counter_path, {})
    if counter.get("week") != week_label(moment):
        counter = {"week": week_label(moment), "calls": 0}
    limit = DEFAULT_BUDGET
    raw = env("MAX_LLM_CALLS_PER_WEEK")
    if raw:
        try:
            limit = int(raw)
        except ValueError:
            print(f"WARNING: MAX_LLM_CALLS_PER_WEEK is not a number ({raw!r}) — "
                  f"using {limit}")
    return counter, limit


# ------------------------------------------------------------------------- the LLM


def api_url():
    base = env("LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    return base + API_PATH


def _single_call(model, messages, api_key):
    """One HTTP call. Returns (text, retryable)."""
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    request = urllib.request.Request(api_url(), data=body, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/zeynelgun-afk/ai-portfolio-experiment",
        "X-Title": "AI Portfolio Experiment - detector",
    })
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"], False
    except urllib.error.HTTPError as error:
        # A 4xx is a caller error — retrying returns the same result. 429 and 5xx are
        # transient.
        retryable = error.code == 429 or error.code >= 500
        print(f"ERROR: LLM HTTP {error.code} ({model})"
              + (" — will retry" if retryable else " — permanent failure"))
        return None, retryable
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"ERROR: LLM network failure ({model}): {error} — will retry")
        return None, True
    except (KeyError, IndexError, ValueError) as error:
        print(f"ERROR: could not read the LLM response ({model}): {error} — will retry")
        return None, True


def extract_json(text):
    """The model may wrap its answer in a ```json block or prose; take the first object."""
    if not text:
        return None
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        raw = raw[4:] if raw.lower().startswith("json") else raw
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return None


def call_llm(*args, **kwargs):
    result = _call_llm(*args, **kwargs)
    payload, status = result
    success = status == "ok"
    scope = kwargs.get("audit_scope")
    if success and scope is claim_audit_scope:
        success = payload.get("status") in VALID_STATUSES and bool(str(payload.get("text", "")).strip())
    elif success and scope is thesis_audit_scope:
        decision = payload.get("decision") or {}
        success = (isinstance(decision, dict) and decision.get("action") in VALID_ACTIONS
                   and bool(str(decision.get("reasoning", "")).strip())
                   and bool(str(decision.get("falsifier", "")).strip()))
    record_result(success)
    return result


def _call_llm(model, system, user, api_key, audit_sources=None, audit_scope=None,
             sleep=None, source_ledger=None, response_validator=None):
    """A JSON-returning LLM call that retries on transient errors and bad output.

    Three problems share one loop, because the remedy for all three is the same: ask
    again.
      1. Network / 429 / 5xx  -> retry with exponential backoff
      2. JSON could not be parsed -> retry, reminding the model what was expected
      3. Unsourced numbers -> number_audit flagged them; retry naming the offending
         figures. A prompt is not a firewall; this gate turns that rule into code.

    `audit_sources`: the texts the numbers are checked against (prompt + old claim).
    Passing nothing disables the number check.
    `audit_scope(output)`: decides WHICH part of the output is audited; returns
    `(text_to_audit, extra_sources)`. The distinction matters: sentences about the market
    need a source, but the DECISION parameters the model produces (shares to sell, a new
    stop level) are not market claims — those are validated by execute_trade.py's
    arithmetic. Conflating the two leaves the model unable to decide anything.

    Returns (payload, status) · status "ok" | "unparseable" | "unsourced_numbers".
    A None payload means the claim MUST NOT be changed.
    """
    sleep = sleep or SLEEP
    messages = [{"role": "system", "content": policy() + "\n\n" + system},
                {"role": "user", "content": user}]
    if source_ledger is not None:
        import evidence
        messages[0]["content"] += "\n" + evidence.INSTRUCTION
        messages[1]["content"] += "\nSOURCE_LEDGER:\n" + json.dumps(source_ledger)
    last_status = "unparseable"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        text, retryable = _single_call(model, messages, api_key)
        if text is None:
            if not retryable or attempt == MAX_ATTEMPTS:
                return None, "unparseable"
            delay = BACKOFF_BASE * (2 ** (attempt - 1))
            print(f"  waiting {delay:.0f}s before retrying ({attempt}/{MAX_ATTEMPTS})")
            sleep(delay)
            continue

        payload = extract_json(text)
        if payload is None:
            last_status = "unparseable"
            if attempt == MAX_ATTEMPTS:
                break
            print(f"  could not extract JSON — asking again with a reminder "
                  f"({attempt}/{MAX_ATTEMPTS})")
            messages += [
                {"role": "assistant", "content": text[:2000]},
                {"role": "user", "content":
                 "Your answer was not valid JSON. Return only the JSON object in the "
                 "requested schema: no prose, no markdown, no code fences."},
            ]
            continue

        if source_ledger is not None and audit_scope in (claim_audit_scope, thesis_audit_scope):
            valid = isinstance(payload, dict)
            if audit_scope is claim_audit_scope:
                valid = valid and set(payload) == {'text', 'status'} and payload.get('status') in VALID_STATUSES and isinstance(payload.get('text'), str) and bool(payload['text'].strip())
            else:
                decision = payload.get('decision') if valid else None
                valid = valid and isinstance(decision, dict) and decision.get('action') in VALID_ACTIONS and all(isinstance(decision.get(k), str) and decision[k].strip() for k in ('reasoning', 'falsifier')) and bool(payload.get('thesis_assessment'))
            if not valid:
                last_status = 'invalid_schema'
                messages.append({'role': 'user', 'content': 'Return exactly the JSON schema in the system message. Required prose and decision fields are missing or invalid. Do not replace the schema with your own.'})
                continue

        if source_ledger is not None:
            try:
                payload = evidence.render_payload(payload, source_ledger)
            except (ValueError, TypeError, AttributeError):
                last_status = "invalid_evidence"
                messages.append({"role": "user", "content": "Evidence validation failed. Use only exact SOURCE_LEDGER references for numeric facts; no raw numeric prose."})
                continue

        if audit_sources and source_ledger is None:
            if audit_scope:
                audited, extra = audit_scope(payload)
            else:
                audited, extra = json.dumps(payload, ensure_ascii=False), ()
            unsourced = number_audit.unsourced_numbers(audited, *audit_sources, *extra)
            if unsourced:
                listed = ", ".join(raw for raw, _ in unsourced)
                last_status = "unsourced_numbers"
                if attempt == MAX_ATTEMPTS:
                    print(f"  UNSOURCED NUMBERS (final attempt): {listed} — "
                          "output rejected")
                    break
                print(f"  UNSOURCED NUMBERS: {listed} — asking for a correction "
                      f"({attempt}/{MAX_ATTEMPTS})")
                messages += [
                    {"role": "assistant", "content": text[:2000]},
                    {"role": "user",
                     "content": number_audit.correction_prompt(unsourced)},
                ]
                continue

        if response_validator is not None:
            try:
                response_validator(payload)
            except (ValueError, TypeError, KeyError, AttributeError) as error:
                last_status = "invalid_schema"
                messages.append({"role": "user", "content": "Proposal validation failed: " + str(error)[:240] + ". Correct the JSON proposal; preserve evidence references."})
                continue
        return payload, "ok"

    return None, last_status


def merge_triggers(items):
    """One claim can be tripped by several conditions at once (price + volume + sector).

    Keying triggers by claim id in a dict overwrote the most informative one (price below
    the 50-day average) with the weakest (the sector ETF at -4.9%). All of them reach the
    prompt.
    """
    return {
        "condition_type": ", ".join(item.get("condition_type", "?") for item in items),
        "measured": "; ".join(f"{i.get('condition_type')}={i.get('measured')}"
                              for i in items),
        "threshold": "; ".join(f"{i.get('condition_type')}={i.get('threshold')}"
                               for i in items),
        "trigger": "; ".join(item.get("trigger", "") for item in items),
    }


# ------------------------------------------------------------------- audit scoping


def claim_audit_scope(payload):
    """code 10: only the claim text is audited; the `status` field holds no numbers."""
    return str(payload.get("text", "")), ()


def thesis_audit_scope(payload):
    """code 20: prose is audited; decision parameters are not, but they ARE sources.

    The decision parameters (shares, amount_usd, new_stop) are the model's decision, not
    an assertion about the market. They must be able to appear in the reasoning sentence
    ("moving the stop to 820"), so they join the allowed set; whether they are correct is
    tested arithmetically in execute_trade.py.
    """
    decision = payload.get("decision") or {}
    prose = " ".join(str(payload.get(field, "")) for field in
                     ("thesis_assessment", "new_thesis_summary", "saturday_note"))
    prose += " " + " ".join(str(decision.get(field, "")) for field in
                            ("reasoning", "falsifier"))
    parameters = " ".join(str(decision.get(field, "")) for field in
                          ("shares", "amount_usd", "new_stop"))
    return prose, (parameters,)


# ------------------------------------------------------------------------- prompts

SYSTEM_COMMON = """You are the intraday reassessment layer of the "AI Portfolio Experiment".
The experiment's charter (RULES.md) places no constraint on your decisions; it places
constraints on the honesty of the record:

- NEVER INVENT A NUMBER. Use only the figures in the data block you are given. Do not
  write a price, market share, product name, analyst target or P/E from memory. If a
  number is not in the data block, it does not belong in your sentence; state the thesis
  without numbers if you must.
- When you write a percentage, name its base (against entry / against the previous close).
- A wish is not a thesis. "Could recover", "earnings may come in strong", "I will wait and
  see" are forbidden. A thesis is a single present-tense sentence tied to evidence.
- Changing your mind is allowed; changing it silently is not. If you are departing from
  the old claim, say that you are.
- Answer with VALID JSON ONLY. No prose, no markdown, no code fences."""

SYSTEM_CLAIM = SYSTEM_COMMON + """

Your task: rewrite THE SINGLE CLAIM you are given. You are not assessing the whole
position and you are not proposing a trade. Only whether this claim's text is still true,
and how it should read given the data that triggered this.

Schema:
{"text": "<one paragraph: the current claim, incorporating the triggering data>",
 "status": "valid" | "weakened" | "invalid"}

What the statuses mean: valid = the claim stands, the data did not break it.
weakened = the claim is still defensible but its evidence has thinned.
invalid = the claim is no longer true."""

SYSTEM_THESIS = SYSTEM_COMMON + """

Your task: re-evaluate this position's WHOLE thesis and produce an executable decision.
The decision is yours; HOLD is a valid decision. You are not the one executing it — a
deterministic script will — so the share and amount fields must be complete and stay
within the cash and share limits stated in the data block.

Schema:
{"thesis_assessment": "<where the thesis stands, what the triggering data changed>",
 "new_thesis_summary": "<one sentence: the current thesis>",
 "claim_statuses": {"<claim_id>": "valid" | "weakened" | "invalid"},
 "decision": {
   "action": "HOLD" | "BUY" | "SELL" | "TRIM",
   "shares": <for SELL/TRIM, the number of shares to sell; null for HOLD/BUY>,
   "amount_usd": <for BUY, the cash to spend; null otherwise>,
   "new_stop": <a number if the stop level changes, null if it does not>,
   "reasoning": "<why this decision — tied to the triggering data>",
   "falsifier": "<what I would have to see to know this decision was wrong>"
 },
 "saturday_note": "<a note to carry into the weekly round; empty string if none>"}

TRIM = sell part of the position (give shares). SELL = sell all of it (shares = every
share held). BUY = add to the position (amount_usd, at most the available cash)."""


def claim_prompt(symbol, position, claim, trigger, data, holding, moment):
    row = data.get(symbol, {})
    lines = [
        f"Time (UTC): {iso(moment)}",
        f"Symbol: {symbol}",
        f"Thesis summary for the position: {position.get('thesis_summary', '-')}",
        "",
        f"THE CLAIM TO REWRITE ({claim['id']}):",
        f"  text: {claim.get('text', '-')}",
        f"  current status: {claim.get('status', '-')}",
        f"  last updated: {claim.get('last_updated', '-')}",
        "",
        "TRIGGERING DATA (threshold crossed, confirmed on 2 consecutive checks):",
        f"  condition type: {trigger.get('condition_type')}",
        f"  measured: {trigger.get('measured')} · threshold: {trigger.get('threshold')}",
        f"  summary: {trigger.get('trigger')}",
        "",
        "CURRENT DATA:",
        f"  price: {row.get('price')} $ (source: {row.get('data_source')})",
        f"  previous close: {row.get('previous_close')} $",
        f"  earnings date: {row.get('earnings_date') or 'none'}",
    ]
    if row.get("volume") and row.get("volume_avg_20d"):
        lines.append(f"  volume / 20d average: "
                     f"{row['volume'] / row['volume_avg_20d']:.2f}x")
    if holding:
        lines += [
            f"  entry price: {holding.get('entry_price')} $",
            f"  shares: {holding.get('shares')}",
            f"  stop_weekly_close: {holding.get('stop_weekly_close')} $",
        ]
    if row.get("news_assessments") or row.get("source_documents"):
        lines += ["NEWS SOURCE EVIDENCE:", json.dumps({"assessments":row.get("news_assessments"),"documents":row.get("source_documents")})]
    if row.get("fundamental_research"):
        lines += ["DATED FUNDAMENTAL EVIDENCE:", json.dumps(row["fundamental_research"])]
    return "\n".join(lines)


def thesis_prompt(symbol, position, triggers, data, holding, cash, moment):
    row = data.get(symbol, {})
    lines = [
        f"Time (UTC): {iso(moment)}",
        f"Symbol: {symbol}",
        f"Current thesis summary: {position.get('thesis_summary', '-')}",
        "",
        "CURRENT CLAIMS:",
    ]
    for claim in position.get("claims", []):
        lines.append(f"  [{claim['id']}] ({claim.get('status')}) {claim.get('text')}")
    lines += ["", "TRIGGERS (confirmed):"]
    for item in triggers:
        lines.append(f"  {item.get('claim_id')} · {item.get('condition_type')}: "
                     f"{item.get('trigger')} (threshold {item.get('threshold')})")
    lines += [
        "",
        "CURRENT DATA:",
        f"  price: {row.get('price')} $ (source: {row.get('data_source')})",
        f"  previous close: {row.get('previous_close')} $",
        f"  earnings date: {row.get('earnings_date') or 'none'}",
    ]
    if row.get("volume") and row.get("volume_avg_20d"):
        lines.append(f"  volume / 20d average: "
                     f"{row['volume'] / row['volume_avg_20d']:.2f}x")
    for etf in ("SMH", "SPY"):
        etf_row = data.get(etf)
        if etf_row and etf_row.get("price") and etf_row.get("previous_close"):
            change = (etf_row["price"] / etf_row["previous_close"] - 1) * 100
            lines.append(f"  {etf} daily: {change:+.2f}%")
    if holding:
        lines += [
            "",
            "POSITION (portfolio.json):",
            f"  shares: {holding.get('shares')} · entry: {holding.get('entry_price')} $",
            f"  cost: {holding.get('cost_usd')} $",
            f"  stop_weekly_close: {holding.get('stop_weekly_close')} $",
            f"  next earnings: {holding.get('next_earnings')}",
        ]
    lines += ["", f"CASH: {cash} $ (amount_usd in a BUY decision cannot exceed this)"]
    if row.get("news_assessments") or row.get("source_documents"):
        lines += ["NEWS SOURCE EVIDENCE:", json.dumps({"assessments":row.get("news_assessments"),"documents":row.get("source_documents")})]
    if row.get("fundamental_research"):
        lines += ["DATED FUNDAMENTAL EVIDENCE:", json.dumps(row["fundamental_research"])]
    return "\n".join(lines)


# --------------------------------------------------------------------------- writes


def mark_claim(claim, status, trigger_text, moment, new_text=None):
    if new_text:
        claim["text"] = new_text
    claim["status"] = status
    claim["last_updated"] = iso(moment)
    claim["trigger"] = f"{iso(moment)}, trigger: {trigger_text}" if trigger_text else None


def append_note(path, heading, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fresh = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as handle:
        if fresh:
            handle.write("# Notes pending for the Saturday round\n\n"
                         "Intraday reassessment writes here. The weekly round reads "
                         "these notes, acts on them, and deletes the note it acted on "
                         "(WEEKLY_INSTRUCTIONS.md step 9).\n")
        handle.write(f"\n## {heading}\n\n{body}\n")


REJECTION_REASON = {
    "unsourced_numbers": "it insisted on writing unsourced numbers",
    "unparseable": "its output could not be read as JSON",
}


# ---------------------------------------------------------------------------- flows


def evidence_for(data, violations, symbol):
    import evidence
    # Scope to the assessed issuer and sector benchmarks; another issuer cannot
    # supply a convenient matching number. Old prose is never a factual source.
    selected = {s: row for s, row in data.items() if s in {symbol, 'SPY', 'SMH'}}
    return evidence.ledger(selected, violations.get('checked_at'), 'detector/market_data')


def claim_flow(theses, violations, portfolio, moment, model, api_key, counter, limit,
               dry_run, full_review, skip=None):
    """Refresh the affected claims (or, in a full review, all of them) with the fast model.

    `skip`: claim ids already handled at thesis level. Those were assessed by the deep
    model with the full context; rewriting the same claim afterwards with the fast model
    would only narrow that context.
    """
    data = violations.get("data", {})
    blocked = {item["symbol"] for item in violations.get("measurement_errors", [])}
    holdings = {p["symbol"]: p for p in portfolio.get("positions", [])}
    skip = set(skip or ())
    grouped = {}
    for item in violations.get("triggered", []):
        if item.get("severity") == "claim":
            grouped.setdefault(item["claim_id"], []).append(item)
    triggers = {claim_id: merge_triggers(items)
                for claim_id, items in grouped.items()}

    if full_review:
        targets = [(symbol, position, claim, triggers.get(claim["id"], {
            "condition_type": "full_review", "measured": None, "threshold": None,
            "trigger": "daily bulk review (no threshold crossed)"}))
            for symbol, position in theses.items() if not symbol.startswith("_")
            for claim in position.get("claims", []) if claim["id"] not in skip]
    else:
        targets = [(symbol, position, claim, triggers[claim["id"]])
                   for symbol, position in theses.items() if not symbol.startswith("_")
                   for claim in position.get("claims", [])
                   if claim["id"] in triggers and claim["id"] not in skip]

    if not targets:
        print("code 10: no claim to rewrite")
        return [], counter

    updated = []
    for symbol, position, claim, trigger in targets:
        if symbol in blocked:
            mark_claim(claim, "unassessed", "Fundamental evidence unavailable", moment)
            violations.setdefault("assessment_errors", []).append(claim["id"])
            updated.append(claim["id"])
            continue
        if counter["calls"] + 2 > limit:
            print(f"BUDGET: the weekly limit ({limit}) is spent — {claim['id']} skipped; "
                  "only code-20 calls are made from here on")
            break
        prompt = claim_prompt(symbol, position, claim, trigger, data,
                             holdings.get(symbol), moment)
        if dry_run:
            print(f"--- prompt for {claim['id']} ({model}) ---\n{prompt}\n")
            continue
        counter["calls"] += 1
        # Audit sources: the prompt (all data given) plus the claim's previous text
        # (those numbers were already audited in an earlier round).
        payload, status = call_llm(model, SYSTEM_CLAIM, prompt, api_key,
                                   audit_sources=(prompt, claim.get("text", "")),
                                   audit_scope=claim_audit_scope,
                                   source_ledger=evidence_for(data, violations, symbol))
        if not payload or payload.get("status") not in VALID_STATUSES \
                or not str(payload.get("text", "")).strip():
            reason = REJECTION_REASON.get(status, "its output did not match the schema")
            print(f"WARNING {claim['id']}: {reason} — the claim text was NOT CHANGED, "
                  "marked 'unassessed'")
            mark_claim(claim, "unassessed", trigger.get("trigger"), moment)
            violations.setdefault("assessment_errors", []).append(claim["id"])
            updated.append(claim["id"])
            continue
        try:
            from claim_evidence import semantic_review
            counter['calls'] += 1
            review = semantic_review(payload, {symbol:data.get(symbol,{})}, evidence_for(data,violations,symbol),
                            api_key, env('OPENROUTER_MODEL_REVIEW','openai/gpt-4o'))
            violations.setdefault('semantic_reviews', []).append({'symbol':symbol,'claim_id':claim['id'],'review':review})
        except ValueError as error:
            violations.setdefault('semantic_reviews', []).append({'symbol':symbol,'claim_id':claim['id'],'error':str(error)})
            mark_claim(claim, 'unassessed', 'Semantic evidence review incomplete', moment)
            violations.setdefault('assessment_errors',[]).append(claim['id'])
            updated.append(claim['id'])
            continue
        mark_claim(claim, payload["status"], trigger.get("trigger"), moment,
                   str(payload["text"]).strip())
        updated.append(claim["id"])
        print(f"OK {claim['id']} -> {payload['status']}")
    return updated, counter


def thesis_flow(theses, violations, portfolio, moment, model, api_key, counter, dry_run,
                notes_path, decision_path):
    """Thesis level: re-evaluate the whole position, produce an executable decision."""
    data = violations.get("data", {})
    blocked = {item["symbol"] for item in violations.get("measurement_errors", [])}
    holdings = {p["symbol"]: p for p in portfolio.get("positions", [])}
    cash = portfolio.get("cash_usd", 0)
    if not dry_run and os.path.exists(decision_path):
        raise RuntimeError("Unconsumed decision bundle exists; refusing to overwrite it")

    # Symbols with a thesis-level trigger get processed, but ALL of that symbol's
    # triggers reach the prompt — the claim-level ones are part of the context too.
    by_symbol, thesis_symbols = {}, set()
    for item in violations.get("triggered", []):
        by_symbol.setdefault(item["symbol"], []).append(item)
        if item.get("severity") == "thesis":
            thesis_symbols.add(item["symbol"])
    groups = {symbol: by_symbol[symbol] for symbol in thesis_symbols}
    if not groups:
        print("code 20: no thesis-level trigger")
        return [], counter

    decisions = []
    for symbol, triggers in groups.items():
        if symbol in blocked:
            violations.setdefault("assessment_errors", []).append(symbol)
            for claim in theses.get(symbol,{}).get("claims",[]):
                mark_claim(claim,"unassessed","Fundamental evidence unavailable",moment)
            continue
        position = theses.get(symbol)
        if not position:
            continue
        prompt = thesis_prompt(symbol, position, triggers, data, holdings.get(symbol),
                              cash, moment)
        if dry_run:
            print(f"--- thesis prompt for {symbol} ({model}) ---\n{prompt}\n")
            continue
        # The thesis level is not gated by the budget (see the module docstring); the
        # call is still counted.
        counter["calls"] += 1
        previous_texts = tuple(c.get("text", "") for c in position.get("claims", []))
        payload, status = call_llm(
            model, SYSTEM_THESIS, prompt, api_key,
            audit_sources=(prompt, position.get("thesis_summary", "")) + previous_texts,
            audit_scope=thesis_audit_scope,
            source_ledger=evidence_for(data, violations, symbol))
        trigger_text = "; ".join(dict.fromkeys(
            item.get("trigger", "") for item in triggers))

        if not payload or not str(payload.get("thesis_assessment", "")).strip():
            violations.setdefault("assessment_errors", []).append(symbol)
            reason = REJECTION_REASON.get(status, "its output did not match the schema")
            print(f"WARNING {symbol}: {reason} — claims were NOT CHANGED, "
                  "no trade produced")
            for claim in position.get("claims", []):
                mark_claim(claim, "unassessed", trigger_text, moment)
            append_note(notes_path, f"{iso(moment)} · {symbol} · UNASSESSED",
                        f"A thesis-level threshold was crossed ({trigger_text}) but the "
                        f"deep model's output was unusable: {reason}. Claims were left "
                        "unchanged and no trade was made; the decision falls to the "
                        "Saturday round.")
            continue

        try:
            from claim_evidence import semantic_review
            counter['calls'] += 1
            review = semantic_review(payload, {symbol:data.get(symbol,{})}, evidence_for(data,violations,symbol),
                            api_key, env('OPENROUTER_MODEL_REVIEW','openai/gpt-4o'))
            violations.setdefault('semantic_reviews', []).append({'symbol':symbol,'review':review})
        except ValueError as error:
            violations.setdefault('semantic_reviews', []).append({'symbol':symbol,'error':str(error)})
            violations.setdefault('assessment_errors',[]).append(symbol)
            for claim in position.get('claims',[]):
                mark_claim(claim,'unassessed','Semantic evidence review incomplete',moment)
            continue
        statuses = payload.get("claim_statuses") or {}
        for claim in position.get("claims", []):
            proposed = statuses.get(claim["id"])
            triggering = any(item["claim_id"] == claim["id"] for item in triggers)
            if proposed in VALID_STATUSES:
                mark_claim(claim, proposed, trigger_text if triggering else None, moment)
            elif triggering:
                mark_claim(claim, "unassessed", trigger_text, moment)
        if str(payload.get("new_thesis_summary", "")).strip():
            position["thesis_summary"] = str(payload["new_thesis_summary"]).strip()

        decision = payload.get("decision") or {}
        action = str(decision.get("action", "")).upper()
        if action not in VALID_ACTIONS:
            violations.setdefault("assessment_errors", []).append(symbol)
            print(f"WARNING {symbol}: decision.action is invalid ({action!r}) — "
                  "no trade produced")
            action = None
        if action and (not str(decision.get("reasoning", "")).strip()
                       or not str(decision.get("falsifier", "")).strip()):
            violations.setdefault("assessment_errors", []).append(symbol)
            print(f"WARNING {symbol}: reasoning or falsifier missing — no trade produced")
            action = None
        if action:
            decisions.append({
                "symbol": symbol,
                "action": action,
                "shares": decision.get("shares"),
                "amount_usd": decision.get("amount_usd"),
                "new_stop": decision.get("new_stop"),
                "reasoning": str(decision.get("reasoning", "")).strip(),
                "falsifier": str(decision.get("falsifier", "")).strip(),
                "trigger": trigger_text,
                "thesis_assessment": str(payload["thesis_assessment"]).strip(),
                "model": model,
                "time": iso(moment),
            })
            print(f"OK {symbol} thesis re-evaluated -> decision: {action}")

        saturday_note = str(payload.get("saturday_note", "")).strip()
        body = [f"**Trigger:** {trigger_text}",
                "", f"**Thesis assessment:** {payload['thesis_assessment']}"]
        if action:
            body += ["", f"**Intraday decision:** {action}"
                         f" · reasoning: {decision.get('reasoning', '-')}",
                     f"**Falsifier:** {decision.get('falsifier', '-')}"]
        if saturday_note:
            body += ["", f"**Note for the Saturday round:** {saturday_note}"]
        append_note(notes_path, f"{iso(moment)} · {symbol} · THESIS LEVEL",
                    "\n".join(body))

    if decisions and not dry_run:
        write_json(decision_path, {"time": iso(moment),
                                  "measurement_at": violations.get("checked_at"),
                                  "decisions": decisions})
        print(f"{len(decisions)} decision(s) written to state/pending_decision.json "
              "(execution happens in execute_trade.py)")
    return decisions, counter


def main():
    parser = argparse.ArgumentParser(
        description="Rewrite the triggered claims or theses")
    parser.add_argument("--code", type=int, default=0,
                        help="detector.py's exit code (10/20)")
    parser.add_argument("--full-review", action="store_true",
                        help="review every claim in bulk with the fast model")
    parser.add_argument("--dry-run", action="store_true",
                        help="make no LLM calls; print the prompts")
    parser.add_argument("--state-dir", default=os.path.join(BASE, "state"))
    args = parser.parse_args()

    api_key = env("OPENROUTER_API_KEY")
    if not api_key and not args.dry_run:
        print("No OPENROUTER_API_KEY — reassessment skipped (the detector keeps "
              "measuring; only the commentary is not refreshed)")
        return 1

    moment = now_utc()
    theses = read_json(THESES_PATH, {})
    portfolio = read_json(PORTFOLIO_PATH, {"positions": [], "cash_usd": 0})
    violations = read_json(os.path.join(args.state_dir, "violations.json"), {})
    if not violations:
        print("state/violations.json is missing — detector.py must run first")
        return 1

    if not args.dry_run:
        write_json(os.path.join(BASE, 'output', 'intraday_evidence.json'), {
            'measurement': violations,
            'ledgers': {symbol: evidence_for(violations.get('data', {}), violations, symbol) for symbol in theses if not symbol.startswith('_')}})

    counter_path = os.path.join(args.state_dir, "llm_counter.json")
    notes_path = os.path.join(args.state_dir, "pending_notes.md")
    decision_path = os.path.join(args.state_dir, "pending_decision.json")
    cooldown_path = os.path.join(args.state_dir, "cooldown.json")
    counter, limit = budget_state(counter_path, moment)
    budget_spent = counter["calls"] >= limit
    if budget_spent:
        print(f"BUDGET SPENT: {counter['calls']}/{limit} calls used in "
              f"{week_label(moment)} — only code-20 calls will be made")

    fast = env("OPENROUTER_MODEL_FAST", DEFAULT_FAST_MODEL)
    deep = env("OPENROUTER_MODEL_DEEP", DEFAULT_DEEP_MODEL)
    updated, decisions = [], []

    # Claims handled at thesis level are not rewritten again by the fast model.
    thesis_symbols = {item["symbol"] for item in violations.get("triggered", [])
                      if item.get("severity") == "thesis"}
    thesis_claims = {claim["id"] for symbol in thesis_symbols
                     for claim in theses.get(symbol, {}).get("claims", [])}
    if args.code >= 20:
        decisions, counter = thesis_flow(theses, violations, portfolio, moment, deep,
                                         api_key, counter, args.dry_run, notes_path,
                                         decision_path)
    # A single run can trip both levels; both are processed.
    if (args.code >= 10 or args.full_review) and not budget_spent:
        updated, counter = claim_flow(theses, violations, portfolio, moment, fast,
                                      api_key, counter, limit, args.dry_run,
                                      args.full_review, skip=thesis_claims)

    if args.dry_run:
        return 0

    if updated or decisions or violations.get("assessment_errors"):
        write_json(THESES_PATH, theses)
        cooldown = read_json(cooldown_path, {})
        for claim_id in updated:
            failed = any(c["id"] == claim_id and c.get("status") == "unassessed"
                         for p in theses.values() if isinstance(p, dict)
                         for c in p.get("claims", []))
            if not failed:
                cooldown[claim_id] = iso(moment)
        for decision in decisions:
            cooldown[f"thesis:{decision['symbol']}"] = iso(moment)
        for item in violations.get('triggered', []):
            if item.get('cooldown_key','').startswith('fundamental:'):
                successful = (item['claim_id'] in updated or any(d['symbol']==item['symbol'] for d in decisions))
                failed = item['symbol'] in violations.get('assessment_errors',[]) or item['claim_id'] in violations.get('assessment_errors',[])
                if successful and not failed:
                    cooldown[item['cooldown_key']] = iso(moment)
        write_json(cooldown_path, cooldown)
    write_json(counter_path, counter)
    write_json(os.path.join(args.state_dir, "violations.json"), violations)
    write_json(os.path.join(BASE, "output", "intraday_evidence.json"), {
        "measurement": violations,
        "ledgers": {symbol: evidence_for(violations.get("data", {}), violations, symbol) for symbol in theses if not symbol.startswith("_")}})
    failed_news = {item["symbol"] for item in violations.get("triggered", [])
                   if item.get("claim_id") == "news_shock"
                   and item["symbol"] in violations.get("assessment_errors", [])}
    if failed_news:
        news_path = os.path.join(args.state_dir, "last_news.json")
        cursors = read_json(news_path, {})
        previous = violations.get("news_previous", {})
        for symbol in failed_news:
            if symbol in previous:
                cursors[symbol] = previous[symbol]
            else:
                cursors.pop(symbol, None)
        write_json(news_path, cursors)

    gh_output = env("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as handle:
            handle.write(f"updated_claims={','.join(updated)}\n")
            handle.write(f"decision_count={len(decisions)}\n")
            handle.write(f"error_count={len(violations.get('assessment_errors', []))}\n")
            handle.write(f"llm_calls={counter['calls']}/{limit}\n")
    print(f"Weekly LLM calls: {counter['calls']}/{limit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
