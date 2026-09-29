"""Expanded, price-blind small-cap earnings event study. Exploratory; never routes trades."""
import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import mean, median
import pandas as pd
import pandas_market_calendars as calendars
import market_data
from earnings_study import classify

CAP_MIN, CAP_MAX = 200_000_000, 5_000_000_000
WINDOW_DAYS = 1500
SEED = 'earnings-change-study-v1'
BENCHMARK_BY_SECTOR = {'Technology':'XLK','Industrials':'XLI','Health Care':'XLV','Healthcare':'XLV',
                       'Consumer Cyclical':'XLY','Consumer Defensive':'XLP','Energy':'XLE',
                       'Financial Services':'XLF','Basic Materials':'XLB','Real Estate':'XLRE',
                       'Utilities':'XLU','Communication Services':'XLC'}
COST_BPS = (0, 25, 100, 250, 500)


def finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)


def safe_rows(rows,symbol,datefield='date'):
    output=[]
    for r in rows:
        try:d=date.fromisoformat(str(r[datefield])[:10])
        except (ValueError,KeyError,TypeError):continue
        if r.get('symbol') != symbol:continue
        output.append((d,r))
    output.sort(key=lambda x:x[0])
    return output


def history(symbol, now):
    # FMP EOD data is split/dividend adjusted by the stable dividend-adjusted endpoint.
    start=(now.date()-timedelta(days=WINDOW_DAYS+90)).isoformat()
    params={'symbol':symbol,'from':start,'to':now.date().isoformat()}
    rows=market_data.fmp('historical-price-eod/dividend-adjusted',**params)
    if any(r.get('symbol')!=symbol for r in rows):raise market_data.ProviderError('History issuer mismatch')
    frame=pd.DataFrame(rows)
    if frame.empty or not {'date','adjClose'}<=set(frame):raise market_data.ProviderError('Missing adjusted prices')
    frame['date']=pd.to_datetime(frame['date'],errors='raise').dt.tz_localize(None)
    frame=frame.rename(columns={'adjClose':'price'}).set_index('date').sort_index()
    frame['price']=pd.to_numeric(frame['price'],errors='coerce')
    if frame.index.has_duplicates or frame['price'].isna().any() or (frame['price']<=0).any():
        raise market_data.ProviderError('Invalid adjusted prices')
    return frame[['price']]


def sequential_features(event, statements, eventday, include_same_day=False):
    """Compare the event quarter with the same fiscal quarter a year earlier."""
    try:
        period=event['period'];year=int(event['fiscalYear'])
    except (KeyError,TypeError,ValueError):return {'status':'period_unavailable'}
    # Prevent using filings published after the market event to label the event.
    available=[]
    for r in statements:
        stamp=(r.get('acceptedDate') or r.get('filingDate') or '')
        try:
            if (date.fromisoformat(str(stamp)[:10]) < eventday or
                (include_same_day and date.fromisoformat(str(stamp)[:10]) == eventday)):available.append(r)
        except (ValueError,TypeError):continue
    matched=[r for r in available if r.get('period')==period]
    byyear={}
    for r in matched:
        try:y=int(r['fiscalYear'])
        except (ValueError,KeyError,TypeError):continue
        if y<=year and y not in byyear:byyear[y]=r
    current,prior=byyear.get(year),byyear.get(year-1)
    if not current or not prior:return {'status':'prior_year_comparison_unavailable'}
    out={'status':'measured','quarter':period,'current_filing_date':current.get('acceptedDate'),
         'prior_filing_date':prior.get('acceptedDate')}
    pairs=(('revenue','revenue'),('grossProfit','grossProfit'),('operatingIncome','operatingIncome'),
           ('operatingCashFlow','operatingCashFlow'))
    for field,name in pairs:
        a,b=current.get(field),prior.get(field)
        if finite(a) and finite(b):
            out[name+'_yoy_change']=a-b
            out[name+'_yoy_pct']=None if b==0 else 100*(a/b-1)
    for row,label in ((current,'current'),(prior,'prior')):
        rev=row.get('revenue');gp=row.get('grossProfit')
        if finite(rev) and rev>0 and finite(gp):out[label+'_gross_margin_pct']=100*gp/rev
    if 'current_gross_margin_pct' in out and 'prior_gross_margin_pct' in out:
        out['gross_margin_yoy_change_pp']=out['current_gross_margin_pct']-out['prior_gross_margin_pct']
    return out


def windows(eventday, days, last):
    after=days[days>pd.Timestamp(eventday)]
    if len(after)<61:return None
    # Next-session close is used as a deliberately delayed, observable entry proxy.
    entry=after[0]
    i=days.get_loc(entry)
    result={'20':days[i+19],'60':days[i+59]}
    if result['60']>last:return None
    return entry,result


def returns(frame, benchmark, sessions, entry,end,costs):
    days=sessions[(sessions>=entry)&(sessions<=end)]
    def series(source):
        if isinstance(source,dict):
            source=pd.Series({pd.Timestamp(k):v.get('price') for k,v in source.items()})
        elif isinstance(source,pd.DataFrame):source=source['price']
        return source.reindex(days)
    s=series(frame);b=series(benchmark)
    # EOD endpoints are exchange days; reject gaps inside the actual exchange session index below.
    if s.isna().any() or b.isna().any() or len(days)<2:return None
    gross=100*(s.iloc[-1]/s.iloc[0]-1)
    bm=100*(b.iloc[-1]/b.iloc[0]-1)
    return {'gross_pct':gross,'excess_benchmark_pp':gross-bm,
            'max_close_drawdown_pct':100*float((s/s.cummax()-1).min()),
            'net_pct_by_assumed_roundtrip_bps':{str(c):gross-c/100 for c in costs}}


def event_features(row, statements):
    group=classify(row)
    f=sequential_features(row,statements,date.fromisoformat(str(row['date'])[:10]))
    if f['status']!='measured':return group,f
    # Predeclared, interpretable indicators. Preserve mixed directions; no fitted score.
    rev=f.get('revenue_yoy_pct'); gm=f.get('gross_margin_yoy_change_pp')
    ocf=f.get('operatingCashFlow_yoy_change')
    indicators={'revenue_positive_yoy':None if rev is None else rev>0,
                'gross_margin_expanding':None if gm is None else gm>0,
                'operating_cash_flow_improving':None if ocf is None else ocf>0}
    f['operating_indicators']=indicators
    known=[v for v in indicators.values() if v is not None]
    f['operating_improvement_group']=('improving' if len(known)>=2 and all(known) else
        'deteriorating' if len(known)>=2 and not any(known) else
        'mixed_or_incomplete')
    return group,f


def evaluate_filing_events(payload, now, sessions, last, costs=COST_BPS):
    events=[]
    for symbol, profile in sorted(payload['profiles'].items()):
        statements=payload['statements'].get(symbol,[])
        if symbol not in payload['prices']:continue
        for row in statements:
            stamp=row.get('acceptedDate') or row.get('filingDate')
            try:eventday=date.fromisoformat(str(stamp)[:10])
            except (TypeError,ValueError):continue
            if not now.date()-timedelta(days=WINDOW_DAYS)<=eventday<=now.date():continue
            cap=next((v for d,v in payload['market_caps'].get(symbol,[])
                      if date.fromisoformat(d)<=eventday),None)
            if not finite(cap) or not CAP_MIN<=cap<=CAP_MAX:continue
            label={'period':row.get('period'),'fiscalYear':row.get('fiscalYear')}
            feature=sequential_features(label,statements,eventday,include_same_day=True)
            if feature.get('status')=='measured':
                indicators={'revenue_positive_yoy':None if feature.get('revenue_yoy_pct') is None else feature['revenue_yoy_pct']>0,
                    'gross_margin_expanding':None if feature.get('gross_margin_yoy_change_pp') is None else feature['gross_margin_yoy_change_pp']>0,
                    'operating_cash_flow_improving':None if feature.get('operatingCashFlow_yoy_change') is None else feature['operatingCashFlow_yoy_change']>0}
                known=[v for v in indicators.values() if v is not None]
                feature['operating_indicators']=indicators
                feature['operating_improvement_group']=('improving' if len(known)>=2 and all(known) else
                    'deteriorating' if len(known)>=2 and not any(known) else 'mixed_or_incomplete')
            baseline=windows(eventday,sessions,last)
            result={'symbol':symbol,'sector':profile.get('sector'),'filing_date':eventday.isoformat(),
                    'filing_timestamp':stamp,'fiscal_period':row.get('period'),'fiscal_year':row.get('fiscalYear'),
                    'event_market_cap_usd':cap,'operating_change':feature}
            if not baseline:
                result['status']='incomplete_price_window';events.append(result);continue
            entry,horizons=baseline;result['entry_date']=entry.date().isoformat();result['outcomes']={}
            benchmark=BENCHMARK_BY_SECTOR.get(profile.get('sector'),'IWM')
            for name in dict.fromkeys(('IWM',benchmark)):
                if name not in payload['prices']:
                    result['status']='missing_benchmark';break
                result['outcomes'][name]={h:returns(payload['prices'][symbol],payload['prices'][name],sessions,entry,end,costs)
                                          for h,end in horizons.items()}
            if 'status' not in result:result['status']='exploratory_only'
            events.append(result)
    return events


def evaluate(payload, now, costs=COST_BPS):
    schedule=calendars.get_calendar('NYSE').schedule(
        start_date=(now.date()-timedelta(days=WINDOW_DAYS+90)),end_date=now.date())
    days=schedule.index.tz_localize(None)
    close=schedule['market_close']
    done=schedule.index[close<=now]
    if len(done)==0:raise ValueError('No completed market sessions')
    last=done[-1].tz_localize(None)
    all_symbols=set(payload['profiles'])
    required_benchmarks={BENCHMARK_BY_SECTOR.get(r.get('sector'),'IWM') for r in payload['profiles'].values()}
    required_benchmarks.add('IWM')
    results=[]
    for symbol in sorted(all_symbols):
        profile=payload['profiles'][symbol]
        rows=safe_rows(payload['earnings'].get(symbol,[]),symbol)
        reports=safe_rows(payload['statements'].get(symbol,[]),symbol)
        statements=[r for _,r in reports]
        for i,(eventday,row) in enumerate(rows):
            if eventday<(now.date()-timedelta(days=WINDOW_DAYS)) or eventday>now.date():continue
            record={'symbol':symbol,'event_date':str(eventday),'sector':profile.get('sector'),
                    'event_market_cap_usd':next((v for d,v in payload['market_caps'].get(symbol,[])
                                                   if date.fromisoformat(d)<=eventday),None)}
            record['earnings_surprise_group'],record['operating_change']=event_features(row,statements)
            if (not finite(record['event_market_cap_usd']) or
                    not CAP_MIN<=record['event_market_cap_usd']<=CAP_MAX):
                record['status']='outside_or_unknown_historical_cap';results.append(record);continue
            if row.get('symbol')!=symbol or sum(d==eventday for d,_ in rows)!=1:
                record['status']='duplicate_or_wrong_issuer';results.append(record);continue
            baseline=windows(eventday,days,last)
            if not baseline or symbol not in payload['prices']:
                record['status']='incomplete_price_window';results.append(record);continue
            entry,horizons=baseline;record['entry_date']=entry.date().isoformat();record['outcomes']={}
            missing=[]
            for benchmark_name in ('IWM',BENCHMARK_BY_SECTOR.get(profile.get('sector'),'IWM')):
                if benchmark_name not in payload['prices']:
                    missing.append(benchmark_name)
            if missing:
                record['status']='missing_benchmark:'+','.join(missing);results.append(record);continue
            for h,end in horizons.items():
                record['outcomes'][h]={name:returns(payload['prices'][symbol],payload['prices'][name],days,entry,end,costs)
                                       for name in dict.fromkeys(('IWM',BENCHMARK_BY_SECTOR.get(profile.get('sector'),'IWM')))}
            if i+1<len(rows):
                nextday=rows[i+1][0]
                if nextday<=last.date():
                    exitday=days[days<pd.Timestamp(nextday)][-1]
                    if exitday>=entry:
                        record['outcomes']['before_next_earnings']={name:returns(payload['prices'][symbol],payload['prices'][name],days,entry,exitday,costs)
                            for name in dict.fromkeys(('IWM',BENCHMARK_BY_SECTOR.get(profile.get('sector'),'IWM')))}
            record['status']='exploratory_only';results.append(record)
    report={'status':'exploratory_only','strategy_validated':False,'as_of':now.isoformat(),
            'event_universe':'active transcript-covered US-listed common-equity proxy; survivorship bias remains',
            'size_definition_usd':[CAP_MIN,CAP_MAX],'entry':'next NYSE session CLOSE; delayed conservative proxy',
            'horizons_sessions':[20,60,'before_next_earnings'],'assumed_roundtrip_cost_bps':list(costs),
            'limitations':['Historical analyst-consensus vintages are not stored; FMP estimates may be revised.',
             'Earnings-release events and SEC filing events are different; filing study is anchored at acceptedDate.',
             'Statements downloaded today can include retrospective vendor restatements; original filed-value vintages are not preserved.',
             'Survivorship and transcript coverage bias; no delisted issuers.',
             'News/call release timestamps are missing; future text labels are not evaluated by this panel.',
             'Assumed transaction costs are not measured spreads or market impact.',
             'Overlapping events per issuer and common dates violate independent-event assumptions.',
             'Operating indicators are historical financial measures, not a causal forecast.',
             'Sector ETF controls are coarse and not issuer-matched.'], 'events':results}
    report['filing_events']=evaluate_filing_events(payload,now,days,last,costs)
    return report


def _valid_us_profile(symbol, rows):
    if len(rows)!=1:return None
    r=rows[0]
    if r.get('symbol')!=symbol or str(r.get('country','')).strip().lower() not in {'us','usa','united states'}:return None
    if r.get('isEtf') or r.get('isFund') or r.get('isAdr') or r.get('isActivelyTrading') is False:return None
    if not finite(r.get('marketCap')) or not CAP_MIN<=r['marketCap']<=CAP_MAX:return None
    if not r.get('sector') or r.get('currency')!='USD':return None
    return r


def collect(max_scan, target, out):
    now=datetime.now(timezone.utc)
    available=market_data.fmp('earnings-transcript-list',allow_empty=True)
    candidates=[]
    for r in available:
        s=r.get('symbol','')
        if not re.fullmatch(r'[A-Z]{1,5}',s) or int(r.get('noOfTranscripts') or 0)<8:continue
        candidates.append(s)
    candidates=sorted(set(candidates),key=lambda s:hashlib.sha256((SEED+s).encode()).hexdigest())[:max_scan]
    payload={'observed_at':now.isoformat(),'selection_seed':SEED,'profiles':{},'earnings':{},
             'statements':{},'market_caps':{},'prices':{},'failures':[],'candidate_count':len(candidates)}
    for symbol in candidates:
        if len(payload['profiles'])>=target:break
        try:
            profile=_valid_us_profile(symbol,market_data.fmp('profile',symbol=symbol,allow_empty=True))
            if not profile:continue
            caps=market_data.fmp('historical-market-capitalization',symbol=symbol,
                **{'from':(now.date()-timedelta(days=WINDOW_DAYS+120)).isoformat(),'to':now.date().isoformat()},allow_empty=True)
            caprows=[]
            for d,r in safe_rows(caps,symbol):
                if finite(r.get('marketCap')):caprows.append([d.isoformat(),r['marketCap']])
            # Ensure at least one covered event-size date in the sample period.
            if not any(CAP_MIN<=v<=CAP_MAX for _,v in caprows):continue
            earn=market_data.fmp('earnings',symbol=symbol,limit=100,allow_empty=True)
            inc=market_data.fmp('income-statement',symbol=symbol,period='quarter',limit=40,allow_empty=True)
            cash=market_data.fmp('cash-flow-statement',symbol=symbol,period='quarter',limit=40,allow_empty=True)
            def issuer(rows):
                if any(x.get('symbol')!=symbol for x in rows):raise market_data.ProviderError('Issuer mismatch')
                return rows
            earn=issuer(earn);inc=issuer(inc);cash=issuer(cash)
            hist=history(symbol,now)
            payload['profiles'][symbol]={k:profile.get(k) for k in ('symbol','companyName','sector','industry','exchangeShortName','marketCap')}
            payload['market_caps'][symbol]=caprows;payload['earnings'][symbol]=earn
            payload['statements'][symbol]=inc
            # Align operating cash flow by fiscal year/period, preserving source rows.
            cashidx={(str(x.get('fiscalYear')),str(x.get('period'))):x.get('operatingCashFlow') for x in cash}
            for statement in inc:
                statement['operatingCashFlow']=cashidx.get((str(statement.get('fiscalYear')),str(statement.get('period'))))
            payload['prices'][symbol]={str(d.date()):{'price':float(v)} for d,v in hist['price'].items()}
            payload['failures'] += []
            print('collected',symbol,len(earn),'events',flush=True)
        except (market_data.ProviderError,ValueError,TypeError,KeyError) as exc:
            payload['failures'].append({'symbol':symbol,'reason':str(exc)})
    # Collect benchmark histories required for sectors represented.
    benchmarks={'IWM'}|{BENCHMARK_BY_SECTOR.get(r.get('sector'),'IWM') for r in payload['profiles'].values()}
    for symbol in sorted(benchmarks-set(payload['prices'])):
        try:
            hist=history(symbol,now)
            payload['prices'][symbol]={str(d.date()):{'price':float(v)} for d,v in hist['price'].items()}
        except market_data.ProviderError as exc:payload['failures'].append({'symbol':symbol,'reason':str(exc)})
    return payload,now


def summarize(report):
    usable=[e for e in report['events'] if e['status']=='exploratory_only' and e['outcomes']]
    groups={}
    for event in usable:
        key=event['operating_change'].get('operating_improvement_group','insufficient_operating_history')
        for horizon,outcomes in event['outcomes'].items():
            for bench,row in outcomes.items():
                if row:groups.setdefault(f'{key}:{horizon}:{bench}',[]).append(row)
    report['summary']={k:{'n':len(v),'median_gross_pct':median(r['gross_pct'] for r in v),
       'median_excess_pp':median(r['excess_benchmark_pp'] for r in v),
       'positive_fraction':mean(int(r['gross_pct']>0) for r in v),
       'median_drawdown_pct':median(r['max_close_drawdown_pct'] for r in v),
       'median_net_pct_by_roundtrip_bps':{c:median(r['net_pct_by_assumed_roundtrip_bps'][c] for r in v)
                                          for c in v[0]['net_pct_by_assumed_roundtrip_bps']}}
       for k,v in sorted(groups.items())}
    report['eligible_events']=len(usable)
    filing_groups={}
    for event in report.get('filing_events',[]):
        if event.get('status')!='exploratory_only':continue
        change=event.get('operating_change',{})
        group=change.get('operating_improvement_group','insufficient_operating_history')
        for benchmark, horizons in event.get('outcomes',{}).items():
            for horizon, result in horizons.items():
                if result:filing_groups.setdefault(f'{group}:{horizon}:{benchmark}',[]).append(result)
    report['filing_summary']={k:{'n':len(v),'median_gross_pct':median(r['gross_pct'] for r in v),
       'median_excess_pp':median(r['excess_benchmark_pp'] for r in v),
       'positive_fraction':mean(int(r['gross_pct']>0) for r in v),
       'median_drawdown_pct':median(r['max_close_drawdown_pct'] for r in v),
       'median_net_pct_by_roundtrip_bps':{c:median(r['net_pct_by_assumed_roundtrip_bps'][c] for r in v)
                                          for c in v[0]['net_pct_by_assumed_roundtrip_bps']}}
       for k,v in sorted(filing_groups.items())}
    # Treat each issuer as one unit for robustness: first average its event outcomes,
    # then summarize across issuers. Also expose leave-one-issuer-out mean excess range.
    filing_cells={}
    for event in report.get('filing_events',[]):
        if event.get('status')!='exploratory_only':continue
        group=event.get('operating_change',{}).get('operating_improvement_group','insufficient_operating_history')
        for bench,horizons in event.get('outcomes',{}).items():
            for horizon,result in horizons.items():
                if result:filing_cells.setdefault(f'{group}:{horizon}:{bench}',{}).setdefault(event['symbol'],[]).append(result)
    balanced={}
    for key, issuers in sorted(filing_cells.items()):
        issuer_rows=[]
        for symbol, rows in sorted(issuers.items()):
            issuer_rows.append({'symbol':symbol,'events':len(rows),
                'mean_gross_pct':mean(r['gross_pct'] for r in rows),
                'mean_excess_pp':mean(r['excess_benchmark_pp'] for r in rows),
                'mean_positive_fraction':mean(int(r['gross_pct']>0) for r in rows),
                'mean_drawdown_pct':mean(r['max_close_drawdown_pct'] for r in rows),
                'mean_net_pct_by_roundtrip_bps':{c:mean(r['net_pct_by_assumed_roundtrip_bps'][c] for r in rows)
                    for c in rows[0]['net_pct_by_assumed_roundtrip_bps']}})
        excess=[r['mean_excess_pp'] for r in issuer_rows]
        balanced[key]={'issuer_n':len(issuer_rows),'median_issuer_mean_gross_pct':median(r['mean_gross_pct'] for r in issuer_rows),
          'median_issuer_mean_excess_pp':median(excess),'mean_issuer_mean_excess_pp':mean(excess),
          'median_issuer_positive_fraction':median(r['mean_positive_fraction'] for r in issuer_rows),
          'median_issuer_mean_drawdown_pct':median(r['mean_drawdown_pct'] for r in issuer_rows),
          'median_issuer_mean_net_pct_by_roundtrip_bps':{c:median(r['mean_net_pct_by_roundtrip_bps'][c] for r in issuer_rows)
            for c in issuer_rows[0]['mean_net_pct_by_roundtrip_bps']},
          'leave_one_issuer_out_mean_excess_pp_range':([min(mean(excess[:i]+excess[i+1:]) for i in range(len(excess))),
             max(mean(excess[:i]+excess[i+1:]) for i in range(len(excess)))] if len(excess)>1 else None),
          'issuers':issuer_rows}
    report['filing_issuer_balanced_summary']=balanced
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--max-scan',type=int,default=120)
    p.add_argument('--target',type=int,default=24)
    p.add_argument('--replay',type=Path,help='Analyse a saved inputs.json snapshot without network access')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if not 1<=a.target<=100 or not a.target<=a.max_scan<=1000:p.error('Require target 1-100 and max-scan target-1000')
    a.output.mkdir(parents=True,exist_ok=False)
    if a.replay:
        encoded=a.replay.read_bytes();payload=json.loads(encoded)
        for symbol,rows in payload['prices'].items():
            payload['prices'][symbol]=(lambda f: f.set_axis(pd.to_datetime(f.index),axis=0).sort_index())(pd.DataFrame.from_dict(rows,orient='index'))
        now=datetime.fromisoformat(payload['observed_at'])
    else:
        payload,now=collect(a.max_scan,a.target,a.output)
        encoded=json.dumps(payload,indent=2,allow_nan=False).encode()
        (a.output/'inputs.json').write_bytes(encoded)
    report=evaluate(payload,now)
    report['inputs_sha256']=hashlib.sha256(encoded).hexdigest()
    report['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['failures']=payload['failures']
    report=summarize(report)
    if not a.replay:(a.output/'inputs.json').write_bytes(encoded)
    (a.output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'profiles':len(payload['profiles']),'events':report['eligible_events'],
                      'summary':report['summary'],'filing_summary':report['filing_summary'],'failures':len(payload['failures'])},indent=2))


if __name__=='__main__':main()
