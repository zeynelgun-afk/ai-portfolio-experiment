"""Prospective research cohorts and advisory exposure checks, separate from prompt health."""
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
import hashlib
import json
import math

import market_data
from execute_trade import read_json, write_json

BASE=Path(__file__).resolve().parent
HORIZONS=(20,60,120)
ROUND_TRIP_COST_SCENARIOS_BPS=(0,25,50,100,250)


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
                      'research':data[symbol].get('research_team_dossier',{}),
                      'evidence_snapshot':{
                          'fundamental_research':data[symbol].get('fundamental_research'),
                          'analyst_revisions':data[symbol].get('analyst_revisions'),
                          'source_documents':data[symbol].get('source_documents',{}),
                          'news_titles':data[symbol].get('news_titles',[]),
                          'providers':data[symbol].get('providers',{})}}
    payload={'round_id':round_id,'observed_at':moment.isoformat(),'candidates':rows,
             'benchmarks':benchmark_quotes,'risk':risk,
             'research_models':data.get('_meta',{}).get('research_models',{}),
             'limits':'Selected research universe only; channel groups overlap. Forward returns use provider split/dividend adjustment when available; not causal agent contribution or portfolio returns.'}
    payload['snapshot']=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    return payload


def _session_days(start, count):
    end=start+timedelta(days=max(240, count*3))
    schedule=market_data.calendars.get_calendar('NYSE').schedule(
        start_date=start+timedelta(days=1),end_date=end)
    return list(schedule.index.date[:count])


def _daily_values(frame, start, end, entry_price):
    if frame is None:return None
    if {'raw_close','total_close'} <= set(frame.columns):
        opening=frame.loc[frame.index.date==start]
        closing=frame.loc[frame.index.date==end]
        if len(opening)!=1 or len(closing)!=1:return None
        base=float(opening['total_close'].iloc[0]);raw=float(opening['raw_close'].iloc[0])
        entry_price=entry_price or raw
        if min(base,raw,entry_price)<=0:return None
        rows=frame.loc[(frame.index.date>=start)&(frame.index.date<=end)]
        wealth=rows['total_close'].astype(float)/base*(raw/entry_price)
    elif 'Close' in frame.columns:
        opening=frame.loc[frame.index.date==start]
        closing=frame.loc[frame.index.date==end]
        if len(closing)!=1:return None
        if entry_price is None:
            if len(opening)!=1:return None
            entry_price=float(opening['Close'].iloc[0])
        if entry_price<=0:return None
        rows=frame.loc[(frame.index.date>=start)&(frame.index.date<=end)]
        wealth=rows['Close'].astype(float)/entry_price
    else:return None
    if wealth.empty or not all(math.isfinite(float(value)) and value>0 for value in wealth):return None
    endpoint=float(wealth.iloc[-1])
    peaks=wealth.cummax()
    drawdown=(wealth/peaks-1)*100
    daily=wealth.pct_change().dropna()
    volatility=float(daily.std(ddof=1)*math.sqrt(252)*100) if len(daily)>1 else None
    return {'wealth_multiple':endpoint,'maximum_drawdown_pct':float(drawdown.min()),
            'realized_volatility_annualized_pct':volatility,'risk_observations':len(daily)}


def score(cohort, histories):
    from market_time import session
    start=date.fromisoformat(cohort['observed_at'][:10])
    days=_session_days(start,max(HORIZONS)+1)
    results=[]; pending=[]
    for symbol,row in cohort['candidates'].items():
        for horizon in HORIZONS:
            benchmark=histories.get('SPY')
            if benchmark is None:
                pending.append(f'{symbol}:{horizon}:benchmark unavailable');continue
            if row.get('entry_mode')=='next_session_close':
                baseline=days[0]
                end=days[horizon]
            else:
                baseline=start
                end=days[horizon-1]
            if benchmark.empty or benchmark.index[-1].date() < end:
                pending.append(f'{symbol}:{horizon}:not mature');continue
            symbols=(symbol,'SPY','SMH')
            total_mode=all(histories.get(s) is not None and {'raw_close','total_close'} <= set(histories[s].columns) for s in symbols)
            if not total_mode and any(frame is not None and 'total_close' in frame.columns for frame in histories.values()):
                pending.append(f'{symbol}:{horizon}:missing adjusted endpoint');continue
            prices={}
            paths={}
            for ticker in symbols:
                entry=row.get('entry_price') if ticker==symbol else cohort.get('benchmarks',{}).get(ticker,{}).get('price')
                path=_daily_values(histories.get(ticker),baseline,end,entry)
                if path:
                    paths[ticker]=path;prices[ticker]=path['wealth_multiple']
            if len(prices)!=3:
                pending.append(f'{symbol}:{horizon}:missing endpoint');continue
            ret=100*(prices[symbol]-1)
            bases={s:100*(prices[s]-1) for s in ('SPY','SMH')}
            net_returns={str(bps):ret-bps/100 for bps in ROUND_TRIP_COST_SCENARIOS_BPS}
            results.append({'symbol':symbol,'decision':row['decision'],'channels':row['channels'],
                            'horizon_sessions':horizon,'end_date':end.isoformat(),
                            'basis':'split_dividend_adjusted_reinvestment' if total_mode else 'price_only_legacy',
                            'return_pct':ret,'net_return_scenarios_pct':net_returns,
                            'excess_spy_pp':ret-bases['SPY'],'excess_smh_pp':ret-bases['SMH'],
                            'net_excess_spy_vs_gross_benchmark_pp':{str(bps):net_returns[str(bps)]-bases['SPY'] for bps in ROUND_TRIP_COST_SCENARIOS_BPS},
                            'maximum_drawdown_pct':paths[symbol]['maximum_drawdown_pct'],
                            'realized_volatility_annualized_pct':paths[symbol]['realized_volatility_annualized_pct'],
                            'risk_observations':paths[symbol]['risk_observations']})
    groups={}
    for row in results:
        for channel in row['channels']:
            key=f"{channel}:{row['horizon_sessions']}"
            groups.setdefault(key,[]).append(row)
    summary={}
    for key,rows in groups.items():
        per_symbol={}
        for row in rows:per_symbol.setdefault(row['symbol'],[]).append(row)
        issuer_means={symbol:sum(item['net_return_scenarios_pct']['100'] for item in items)/len(items)
                      for symbol,items in per_symbol.items()}
        summary[key]={'n':len(rows),'unique_symbols':len(per_symbol),
            'mean_return_pct':sum(r['return_pct'] for r in rows)/len(rows),
            'mean_net_return_100bps_pct':sum(r['net_return_scenarios_pct']['100'] for r in rows)/len(rows),
            'issuer_balanced_net_return_100bps_pct':sum(issuer_means.values())/len(issuer_means),
            'mean_excess_spy_pp':sum(r['excess_spy_pp'] for r in rows)/len(rows),
            'mean_maximum_drawdown_pct':sum(r['maximum_drawdown_pct'] for r in rows)/len(rows)}
    return {'round_id':cohort['round_id'],'results':results,'pending':pending,'channel_summary':summary}


def main():
    observations=read_json(str(BASE/'state/research_observations.json'),{})
    analyst_observations=read_json(str(BASE/'state/analyst_revision_observations.json'),{})
    if not observations and not analyst_observations:
        print('No prospective research cohorts yet');return
    symbols={'SPY','SMH'}|{s for c in observations.values() for s in c['candidates']}
    symbols.update(r['symbol'] for r in analyst_observations.values())
    histories={}; failures=[]
    for symbol in sorted(symbols):
        try:histories[symbol]=market_data.return_history(symbol)
        except market_data.ProviderError:failures.append(symbol)
    if analyst_observations:
        from analyst_revisions import publish
        publish(analyst_observations, BASE, histories)
    output={'as_of':datetime.now(timezone.utc).isoformat(),
            'cohorts':[score(c,histories) for c in observations.values()],
            'unavailable_symbols':failures,
            'limits':('20/60/120-session candidate outcomes; cost sensitivities subtract 0/25/50/100/250 bps round-trip from each candidate return. '
                      'These are scenarios, not observed spread/impact. Net excess compares cost-adjusted candidates with gross SPY/SMH references. '
                      'Risk is candidate-path maximum drawdown and annualized realized volatility. Overlapping cohorts are issuer-balanced in a separate summary; '
                      'no causal attribution or proven predictive benefit. Dividends are reinvested in research price series but remain cash/receivables in portfolio accounting.')}
    write_json(str(BASE/'state/research_performance.json'),output)
    lines=['# Prospective research performance','',output['limits'],'',
           '| Round / channel / sessions | n / issuers | Mean gross | Mean net @100bp | Issuer-balanced net @100bp | Mean excess vs SPY | Mean max drawdown |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for cohort in output['cohorts']:
        for channel,item in cohort['channel_summary'].items():
            lines.append(f"| {cohort['round_id']} / {channel} | {item['n']} / {item['unique_symbols']} | {item['mean_return_pct']:.2f}% | {item['mean_net_return_100bps_pct']:.2f}% | {item['issuer_balanced_net_return_100bps_pct']:.2f}% | {item['mean_excess_spy_pp']:.2f} pp | {item['mean_maximum_drawdown_pct']:.2f}% |")
        lines.append(f"\nPending measurements for {cohort['round_id']}: {len(cohort['pending'])}\n")
    (BASE/'RESEARCH_PERFORMANCE.md').write_text('\n'.join(lines)+'\n')
    print('Updated prospective research performance')


if __name__=='__main__':main()
