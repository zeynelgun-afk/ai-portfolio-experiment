"""Prospective split/dividend accounting with atomic replay protection.

No inferred ticker renames, mergers, cash-in-lieu or retroactive trade rewrites.
"""
import copy
from datetime import datetime, date, timezone
import json
import math
import os
from pathlib import Path
import requests
import market_data
from execute_trade import read_json

BASE=Path(__file__).resolve().parent


def events(symbol):
    """An empty successful response is valid; transport failure is never 'no events'."""
    key=os.environ.get('FMP_API_KEY')
    if not key:raise market_data.ProviderError('Corporate actions require FMP credentials')
    result=[]
    for kind,endpoint in [('split','splits'),('dividend','dividends')]:
        try:
            response=requests.get('https://financialmodelingprep.com/stable/'+endpoint,
                                  params={'symbol':symbol,'apikey':key,'limit':1000},timeout=20)
            if response.status_code!=200:raise ValueError('HTTP')
            rows=response.json()
            if not isinstance(rows,list):raise ValueError('schema')
            for row in rows:
                if row.get('symbol')!=symbol:raise ValueError('issuer')
                day=date.fromisoformat(row['date'])
                item={'id':f'{symbol}:{kind}:{day}', 'symbol':symbol,'kind':kind,'date':day.isoformat(),'source':'FMP/'+endpoint}
                if kind=='split':
                    numerator=float(row['numerator']);denominator=float(row['denominator'])
                    if not all(math.isfinite(v) and v>0 for v in (numerator,denominator)):raise ValueError('ratio')
                    item['ratio']=numerator/denominator
                else:
                    amount=float(row['dividend'])
                    if not math.isfinite(amount) or amount<0:raise ValueError('dividend')
                    item.update(amount_per_share=amount,payment_date=row.get('paymentDate') or None)
                    if item['payment_date'] and date.fromisoformat(item['payment_date']) < day:
                        raise ValueError('Unsupported payment before ex-date; manual reconciliation required')
                result.append(item)
        except Exception:
            market_data.event(symbol,'corporate_actions','unavailable','FMP event data unavailable; no equivalent payment-date backup')
            raise market_data.ProviderError('Corporate-action data unavailable for '+symbol) from None
    # Conflicting duplicates cannot silently overwrite amounts/ratios.
    unique={}
    for event in result:
        if event['id'] in unique and unique[event['id']]!=event:raise ValueError('Conflicting corporate action')
        unique[event['id']]=event
    return sorted(unique.values(),key=lambda e:(e['date'],0 if e['kind']=='split' else 1))



def identity(symbol):
    rows = market_data.fmp('profile', symbol=symbol)
    if len(rows) != 1 or rows[0].get('symbol') != symbol:
        raise ValueError('Corporate-action issuer identity unavailable')
    row = rows[0]
    identifier = row.get('isin') or row.get('cik')
    if row.get('currency') != 'USD' or not identifier or row.get('isActivelyTrading') is not True:
        raise ValueError('Unsupported currency or inactive/unknown issuer; manual reconciliation required')
    return {'identifier':str(identifier), 'currency':'USD'}


def reconcile(book, theses, state, feed, today):
    book,theses,state=copy.deepcopy(book),copy.deepcopy(theses),copy.deepcopy(state)
    if not state:
        # Explicit prospective boundary; historical share bases are not guessed.
        state={'baseline_date':today.isoformat(),'checked_through':today.isoformat(),'events':{},'receivables':{}}
        return book,theses,state,[]
    baseline=date.fromisoformat(state['baseline_date'])
    changes=[]
    positions={p['symbol']:p for p in book['positions']}
    for event in sorted(feed,key=lambda e:(e['date'],0 if e['kind']=='split' else 1)):
        day=date.fromisoformat(event['date']);ident=event['id'];symbol=event['symbol']
        if day<=baseline or day>today:continue
        if ident in state['events']:
            prior = state['events'][ident]['event']
            if prior != event:
                # A newly announced payment date does not change entitlement or amount.
                revised = dict(prior, payment_date=event.get('payment_date'))
                if event['kind']=='dividend' and prior.get('payment_date') is None and event.get('payment_date') and revised==event:
                    state['events'][ident]['event']=event
                    if ident in state['receivables']:
                        state['receivables'][ident]['payment_date']=event['payment_date']
                    changes.append({'payment_date_announced':event})
                else:
                    raise ValueError('Provider revised an already accounted event; manual reconciliation required')
            continue
        position=positions.get(symbol)
        # Since workflows reconcile before trading, same-day fills must not predate reconciliation.
        later=[t for t in book.get('trade_history',[]) if t.get('symbol')==symbol and str(t.get('date',''))>=event['date']]
        history=[t for t in book.get('trade_history',[]) if t.get('symbol')==symbol]
        never_held_before=bool(history) and min(str(t.get('date','')) for t in history)>=event['date'] and position and position.get('entry_date','')>=event['date']
        if later and not never_held_before:
            raise ValueError('Late corporate action crosses recorded trades; refusing to guess share entitlement')
        shares=float(position['shares']) if position and position.get('entry_date','')<event['date'] else 0
        if event['kind']=='split':
            ratio=event['ratio']
            if shares:
                position['shares']*=ratio
                position['entry_price']/=ratio
                if position.get('stop_weekly_close'):position['stop_weekly_close']/=ratio
                for claim in theses.get(symbol,{}).get('claims',[]):
                    for condition in claim.get('conditions',[]):
                        if condition.get('type')=='price_below':condition['value']/=ratio
                    claim['status']='unassessed'
                    claim['trigger']='Share split reconciled; revalidate text against the new share basis'
                # cost_usd is invariant; raw trade history remains unchanged.
            changes.append({'event':event,'eligible_shares':shares})
        else:
            if shares:
                state['receivables'][ident]={'symbol':symbol,'amount_usd':shares*event['amount_per_share'],
                    'payment_date':event['payment_date'],'paid':False,'eligible_shares':shares}
            changes.append({'event':event,'eligible_shares':shares})
        state['events'][ident]={'event':event,'eligible_shares':shares}
    for ident,receivable in state['receivables'].items():
        if not receivable['paid'] and receivable['payment_date'] and date.fromisoformat(receivable['payment_date'])<=today:
            book['cash_usd']+=receivable['amount_usd']
            receivable['paid']=True
            changes.append({'cash_dividend':ident,'amount_usd':receivable['amount_usd']})
    book['dividend_receivable_usd']=sum(r['amount_usd'] for r in state['receivables'].values() if not r['paid'])
    state['checked_through']=today.isoformat()
    return book,theses,state,changes


def main():
    from weekly_round import commit_bundle, recover
    recovered = recover(BASE)
    today=datetime.now(timezone.utc).date()
    state=read_json(str(BASE/'state/corporate_actions.json'),{})
    book=read_json(str(BASE/'portfolio.json'),None)
    theses=read_json(str(BASE/'theses.json'),None)
    feed=[]
    symbols={p['symbol'] for p in book['positions']}|{r['symbol'] for r in state.get('receivables',{}).values() if not r['paid']}
    identities=dict(state.get('identities',{}))
    for symbol in sorted(symbols):
        current=identity(symbol)
        if symbol in identities and current!=identities[symbol]:
            raise ValueError('Issuer identity changed; automatic accounting and trading stopped')
        identities[symbol]=current
    if state:
        # Continue checking previously held issuers for late announcements after sale.
        for symbol in sorted(set(identities)|symbols):feed.extend(events(symbol))
    updated,theses,new_state,changes=reconcile(book,theses,state,feed,today)
    if recovered:
        changes.append({'recovery':'Completed an interrupted transaction before reconciliation'})
    new_state['identities']=identities
    if state and identities!=state.get('identities',{}):
        changes.append({'issuer_identities_registered':sorted(set(identities)-set(state.get('identities',{})))})
    if not state:
        basis={}
        for ticker in ('SPY','SMH'):
            series=market_data.return_history(ticker)
            stamp=series.index[-1].date().isoformat()
            value=book['starting_capital_usd']*float(series['raw_close'].iloc[-1])/book['benchmark'][ticker+'_reference']
            basis[ticker]={'date':stamp,'value_usd':value,'provider':series.attrs['provider']}
        updated['benchmark_total_return_basis']=basis
        changes.append({'initialization':'Prospective corporate actions and benchmark return basis; earlier history retained'})
    targets={'state/corporate_actions.json':json.dumps(new_state,indent=2)+'\n'}
    if changes:
        targets.update({'portfolio.json':json.dumps(updated,indent=2)+'\n','theses.json':json.dumps(theses,indent=2)+'\n'})
        log=(BASE/'CORPORATE_ACTIONS.md').read_text() if (BASE/'CORPORATE_ACTIONS.md').exists() else '# Corporate actions\n'
        targets['CORPORATE_ACTIONS.md']=log+'\n## '+today.isoformat()+'\n\n```json\n'+json.dumps(changes,indent=2)+'\n```\n'
    split_symbols={c['event']['symbol'] for c in changes if c.get('event',{}).get('kind')=='split' and c.get('eligible_shares')}
    if split_symbols:
        violations=read_json(str(BASE/'state/violations.json'),{})
        violations['conditions']={k:v for k,v in violations.get('conditions',{}).items() if v.get('symbol') not in split_symbols}
        violations['triggered']=[v for v in violations.get('triggered',[]) if v.get('symbol') not in split_symbols]
        targets['state/violations.json']=json.dumps(violations,indent=2)+'\n'
    commit_bundle(BASE,targets)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as out:out.write('changed='+('true' if changes or not state else 'false')+'\n')
    print('Corporate actions reconciled: '+str(len(changes))+' changes')



if __name__=='__main__':main()
