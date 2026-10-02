"""Versioned decision monitors and code-owned event identities; no trade recommendations."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]


def event_id(symbol, kind, evidence):
    return digest([symbol,kind,evidence])


def deterioration(position):
    claims=position.get('claims',[])
    bad=[c['id'] for c in claims if c.get('status')=='invalid']
    weak=[c['id'] for c in claims if c.get('status')=='weakened']
    return sorted(bad or (weak if len(weak)>=2 else []))


def escalation(symbol, position, previous_statuses):
    affected=deterioration(position)
    if not affected or not any(previous_statuses.get(c['id'])!=c.get('status') for c in position.get('claims',[]) if c['id'] in affected):
        return None
    return {'symbol':symbol,'claim_id':'claim_escalation','severity':'thesis',
            'condition_type':'claim_escalation','measured':len(affected),'threshold':0,
            'trigger':'Claim evidence deteriorated: '+', '.join(affected),
            'cooldown_key':'escalation:'+event_id(symbol,'claims',[(c['id'],c['status'],c['text']) for c in position['claims'] if c['id'] in affected])}


def material_event(trigger, data):
    """Only immutable news or a changed financial report can bypass a daily lock."""
    symbol=trigger['symbol']
    if trigger.get('news_evidence',{}).get('source_documents'):
        return event_id(symbol,'news',sorted(trigger['news_evidence']['source_documents']))
    if trigger.get('condition_type','').startswith('fundamental_'):
        metric=trigger.get('metric')
        fact=data.get(symbol,{}).get('fundamental_research',{}).get('facts',{}).get(metric)
        if fact:
            return event_id(symbol,'financial_report',[metric,fact['as_of'],fact['value'],fact['unit']])
    return None



def material_events(trigger, data):
    documents=trigger.get('news_evidence',{}).get('source_documents',{})
    if documents:
        # Exact syndicated text remains the same event even under another URL/date,
        # and changing the batch grouping does not create a new execution identity.
        cited={c['source_id'] for c in trigger['news_evidence'].get('citations',[]) if c.get('source_id') in documents}
        return sorted({event_id(trigger['symbol'],'news_text',' '.join(documents[key]['text'].split()).casefold()) for key in cited})
    event=material_event(trigger,data)
    return [event] if event else []


def validate_monitoring(monitoring, symbol, old, data, facts, moment, stop_before=None, stop_after=None):
    """Validate a whole thesis/monitor replacement, not just an updated paragraph."""
    from weekly_round import validate_theses
    if not isinstance(monitoring,dict) or set(monitoring)!={'claims','next_review_at','falsifier_condition','change_reason','evidence_ids'}:
        raise ValueError('Monitoring needs claims, next_review_at, falsifier_condition, change_reason and evidence_ids')
    due=datetime.fromisoformat(monitoring['next_review_at'].replace('Z','+00:00'))
    if due.tzinfo is None or not moment < due <= moment+timedelta(days=7):
        raise ValueError('Next review must be a future timezone-aware timestamp within one week')
    if not isinstance(monitoring['change_reason'],str) or not monitoring['change_reason'].strip():
        raise ValueError('Explain the old/new monitoring change or explicitly why it stays unchanged')
    block={'thesis_summary':'Validated separately', 'claims':copy.deepcopy(monitoring['claims'])}
    validate_theses({symbol:block},{'positions':[{'symbol':symbol}]},moment,data)
    ids={c['id']:c for c in monitoring['claims']}
    ref=monitoring['falsifier_condition']
    if not isinstance(ref,dict) or set(ref)!={'claim_id','condition_index'} or ref['claim_id'] not in ids:
        raise ValueError('Falsifier must reference a monitored claim condition')
    index=ref['condition_index']
    conditions=ids[ref['claim_id']]['conditions']
    if type(index) is not int or not 0<=index<len(conditions) or conditions[index]['severity']!='thesis':
        raise ValueError('Falsifier must open a whole-thesis review')
    available={key:value for key,value in facts.items() if value.get('symbol')==symbol}
    available.update(data.get(symbol,{}).get('source_documents',{}))
    references=monitoring['evidence_ids']
    if not isinstance(references,list) or not references or any(not isinstance(k,str) or k not in available for k in references):
        invalid = [k for k in references if not isinstance(k, str) or k not in available] if isinstance(references, list) else references
        raise ValueError('Monitoring changes require supplied issuer-specific evidence IDs; '
                         f'rejected: {invalid!r}; choose from: {sorted(available)}')
    fingerprints={key:digest({k:v for k,v in available[key].items() if k not in {'snapshot','observed_at'}}) for key in references}
    old_by_id={c['id']:c for c in old.get('claims',[])}
    relaxed=set(old_by_id)-set(ids)
    for ident,claim in ids.items():
        before=old_by_id.get(ident,{}).get('conditions',[])
        after=claim['conditions']
        # Removing or changing an existing condition, including its threshold or
        # severity, needs fresh non-price evidence. Adding a monitor does not erase one.
        if any(c not in after for c in before):relaxed.add(ident)
    if relaxed or (stop_before is not None and stop_after is not None and stop_after < stop_before):
        old_evidence=old.get('monitoring',{}).get('evidence_fingerprints',{})
        changed=[k for k in references if fingerprints[k]!=old_evidence.get(k)]
        fundamental_metrics={'revenue_yoy_pct','gross_margin_pct','operating_margin_pct','quarter_operating_cash_flow','quarter_free_cash_flow','net_debt','total_debt'}
        if not any(k.startswith(('news:', 'analyst:')) or available[k].get('metric') in fundamental_metrics for k in changed):
            raise ValueError('Changing/removing old thresholds requires new non-price evidence; price moves alone cannot justify it')
    return dict(copy.deepcopy(monitoring),revision=digest(monitoring),created_at=moment.isoformat(),evidence_fingerprints=fingerprints)


INSTRUCTION='''Every decision must include monitoring with exactly these fields:
claims: the COMPLETE updated claims array, each with EXACTLY {id,text,status,conditions}; keep stable IDs.
Do NOT copy old claim prose or metadata. Rewrite every text using CURRENT evidence. Omit
last_updated, trigger and source fields; code owns these. Use qualitative text or valid
SOURCE_LEDGER placeholders only, never old numeric prose. In falsifier prose describe the
referenced condition qualitatively; its chosen numeric threshold belongs only in value.
Never invent a reference such as SYMBOL.price_below: a condition type is not a fact ID.
If fundamental_research supplies measured metrics, include at least one fundamental_below
or fundamental_above condition per position, with {type,metric,value,unit,severity}.
Supported metrics: revenue_yoy_pct, gross_margin_pct, operating_margin_pct,
quarter_operating_cash_flow, quarter_free_cash_flow, net_debt, total_debt.
For example, a fundamental condition has type fundamental_below, metric operating_margin_pct,
unit %, numeric value of your chosen threshold, and severity thesis. Use actual metric units.
next_review_at: a timezone-aware future ISO timestamp, no later than one week from NOW.
falsifier_condition: {claim_id,condition_index}, pointing to a thesis-severity condition.
change_reason: explain what new evidence changed the old conditions, or why unchanged.
evidence_ids: supplied issuer-specific SOURCE_LEDGER IDs or news source IDs.
Keep raw news source IDs in evidence_ids; in prose identify news by its title or publisher.
Use the existing supported detector condition schema. Positive conditions include
price_above, daily_change_above_pct, sector_etf_above_pct and fundamental_above.
For moving technical reference levels use price_below_sma50_pct, price_above_sma50_pct,
price_below_sma200_pct or price_above_sma200_pct with value as a percent distance.
These use freshly calculated averages; do not freeze a moving average into a fixed price.
A positive signal requests review; it never mandates buying. Keep a concrete downside
falsifier as well. Specify a review date around the next catalyst; when expected evidence
has not arrived by that time, revisit the decision rather than extending it silently.
Update text AND conditions together. Never move thresholds merely to excuse a price loss.
Condition removal or threshold changes require changed non-price evidence and an explicit
old-versus-new explanation. Include all old claims unless new evidence justifies removal.
Your falsifier prose must explain the referenced executable condition. HOLD needs the same
monitoring and accountability as any trade. Dates and thresholds here are chosen parameters,
not observed market facts. Conditions are reviewed by an independent evidence checker.'''


def history_update(history, changes):
    result=copy.deepcopy(history)
    for change in changes:
        result.setdefault(digest(change),copy.deepcopy(change))
    return result
