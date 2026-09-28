"""Prospective research cohorts and advisory exposure checks, separate from prompt health."""
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
import hashlib
import json
import math

import market_data
from execute_trade import read_json, write_json

BASE=Path(__file__).resolve().parent


def exposure(book, quotes, data=None):
    values={p['symbol']:p['shares']*quotes[p['symbol']]['price'] for p in book['positions']}
    total=book['cash_usd']+book.get('dividend_receivable_usd',0)+sum(values.values())
    if not math.isfinite(total) or total <= 0:
        raise ValueError('Invalid portfolio valuation for exposure report')
    weights={s:round(v/total*100,4) for s,v in values.items()}
    correlations={}
    if data:
        import pandas as pd
        names=sorted(values)
        for index,left in enumerate(names):
            for right in names[index+1:]:
                series=pd.DataFrame({s:pd.Series(data.get(s,{}).get('daily_returns',{}),dtype=float) for s in (left,right)}).dropna()
                corr=series[left].corr(series[right]) if len(series)>=20 and all(series[s].std()>0 for s in (left,right)) else None
                correlations[left+'/'+right]={'observations':len(series),'correlation':float(corr) if corr is not None and math.isfinite(corr) else None}
    return {'equity_usd':round(total,2),'weights_pct':weights, 'return_correlations':correlations,
            'largest_position_pct':max(weights.values(),default=0),
            'all_positions_down_20pct_equity_impact_pct':round(-20*sum(values.values())/total,4),
            'largest_position_down_40pct_equity_impact_pct':round(-0.4*max(weights.values(),default=0),4),
            'limits':'Arithmetic stress scenarios, not forecasts or loss limits. No new allocation caps.'}


def observation(round_id, moment, proposal, data, quotes, discovery, benchmark_quotes, risk):
    decisions={r['symbol']:r['action'] for r in proposal['decisions']}
    rows={}
    for symbol in sorted(s for s in data if not s.startswith('_')):
        rows[symbol]={'entry_price':quotes[symbol]['price'],'price_at':quotes[symbol]['price_at'],
                      'provider':quotes[symbol]['price_provider'],
                      'decision':decisions.get(symbol,'WATCH'),
                      'channels':discovery.get('membership',{}).get(symbol,['retained_or_legacy']),
                      'research':data[symbol].get('research_team_dossier',{})}
    payload={'round_id':round_id,'observed_at':moment.isoformat(),'candidates':rows,
             'benchmarks':benchmark_quotes,'risk':risk,
             'research_models':data.get('_meta',{}).get('research_models',{}),
             'limits':'Selected research universe only; channel groups overlap. Forward returns use provider split/dividend adjustment when available; not causal agent contribution or portfolio returns.'}
    payload['snapshot']=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    return payload


def score(cohort, histories):
    from market_time import session
    start=date.fromisoformat(cohort['observed_at'][:10])
    days=[]
    for offset in range(1,61):
        day=start+timedelta(days=offset)
        if session(day):days.append(day)
        if len(days)==20:break
    results=[]; pending=[]
    for symbol,row in cohort['candidates'].items():
        for horizon in (5,20):
            benchmark=histories.get('SPY')
            if benchmark is None:
                pending.append(f'{symbol}:{horizon}:benchmark unavailable');continue
            end=days[horizon-1]
            if benchmark.empty or benchmark.index[-1].date() < end:
                pending.append(f'{symbol}:{horizon}:not mature');continue
            def close(ticker):
                frame=histories.get(ticker)
                if frame is None:return None
                rows=frame.loc[frame.index.date==end]
                return float(rows['Close'].iloc[0]) if len(rows)==1 else None
            total_mode=all({'raw_close','total_close'} <= set(histories.get(s,{}).columns) for s in (symbol,'SPY','SMH') if histories.get(s) is not None) and all(histories.get(s) is not None for s in (symbol,'SPY','SMH'))
            def wealth(ticker,entry):
                frame=histories[ticker]
                opening=frame.loc[frame.index.date==start]
                closing=frame.loc[frame.index.date==end]
                if len(opening)!=1 or len(closing)!=1:return None
                return float(closing['total_close'].iloc[0]/opening['total_close'].iloc[0]*opening['raw_close'].iloc[0]/entry)
            if not total_mode and any('total_close' in frame.columns for frame in histories.values()):
                pending.append(f'{symbol}:{horizon}:missing adjusted endpoint');continue
            if total_mode:
                multiples={s:wealth(s,row['entry_price'] if s==symbol else cohort['benchmarks'][s]['price']) for s in (symbol,'SPY','SMH')}
                prices={s:multiple for s,multiple in multiples.items()}
            else:
                prices={s:close(s) for s in (symbol,'SPY','SMH')}
            if any(v is None or not math.isfinite(v) or v<=0 for v in prices.values()):
                pending.append(f'{symbol}:{horizon}:missing endpoint');continue
            ret=100*(prices[symbol]-1) if total_mode else 100*(prices[symbol]/row['entry_price']-1)
            bases={s:100*(prices[s]-1) if total_mode else 100*(prices[s]/cohort['benchmarks'][s]['price']-1) for s in ('SPY','SMH')}
            results.append({'symbol':symbol,'decision':row['decision'],'channels':row['channels'],
                            'horizon_sessions':horizon,'end_date':end.isoformat(),
                            'basis':'split_dividend_adjusted_reinvestment' if total_mode else 'legacy_price_only',
                            'return_pct':ret,'excess_spy_pp':ret-bases['SPY'],'excess_smh_pp':ret-bases['SMH']})
    groups={}
    for row in results:
        for channel in row['channels']:
            key=f"{channel}:{row['horizon_sessions']}"
            groups.setdefault(key,[]).append(row)
    summary={key:{'n':len(rows),'mean_return_pct':sum(r['return_pct'] for r in rows)/len(rows),
                  'mean_excess_spy_pp':sum(r['excess_spy_pp'] for r in rows)/len(rows)} for key,rows in groups.items()}
    return {'round_id':cohort['round_id'],'results':results,'pending':pending,'channel_summary':summary}


def main():
    observations=read_json(str(BASE/'state/research_observations.json'),{})
    if not observations:
        print('No prospective research cohorts yet');return
    symbols={'SPY','SMH'}|{s for c in observations.values() for s in c['candidates']}
    histories={}; failures=[]
    for symbol in sorted(symbols):
        try:histories[symbol]=market_data.return_history(symbol)
        except market_data.ProviderError:failures.append(symbol)
    output={'as_of':datetime.now(timezone.utc).isoformat(),
            'cohorts':[score(c,histories) for c in observations.values()],
            'unavailable_symbols':failures,
            'limits':'Forward split/dividend-adjusted research returns assume reinvestment via provider-adjusted series. Actual portfolio dividends are cash/receivables. Costs and causal attribution remain unmodeled.'}
    write_json(str(BASE/'state/research_performance.json'),output)
    lines=['# Prospective research performance','',output['limits'],'',
           '| Round / channel / sessions | n | Mean adjusted return | Mean excess vs SPY |',
           '|---|---:|---:|---:|']
    for cohort in output['cohorts']:
        for channel,item in cohort['channel_summary'].items():
            lines.append(f"| {cohort['round_id']} / {channel} | {item['n']} | {item['mean_return_pct']:.2f}% | {item['mean_excess_spy_pp']:.2f} pp |")
        lines.append(f"\nPending measurements for {cohort['round_id']}: {len(cohort['pending'])}\n")
    (BASE/'RESEARCH_PERFORMANCE.md').write_text('\n'.join(lines)+'\n')
    print('Updated prospective research performance')


if __name__=='__main__':main()
