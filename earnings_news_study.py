"""Compare paired-call labels with labels augmented by contemporaneous news only."""
import argparse
from datetime import date, timedelta, datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
import market_data
from earnings_change_study import annotate, summarize


def filter_news(rows, symbol, start, end):
    accepted, rejected, seen = [], [], set()
    for row in rows:
        try:
            day = date.fromisoformat(str(row['publishedDate'])[:10])
        except (ValueError, KeyError):
            rejected.append('missing_or_invalid_publication_date'); continue
        if row.get('symbol') != symbol or not start <= day <= end:
            rejected.append('issuer_or_time_window_mismatch'); continue
        if not row.get('url') or not row.get('text'):
            rejected.append('missing_url_or_text'); continue
        u=urlsplit(row['url'])
        url=urlunsplit((u.scheme,u.netloc,u.path,'',''))
        title=re.sub(r'\W+',' ',row.get('title','').lower()).strip()
        text=re.sub(r'\s+',' ',row['text'].lower()).strip()
        keys={('url',url),('text',text)}
        if title:keys.add(('title',title))
        if seen & keys:
            rejected.append('duplicate'); continue
        seen |= keys
        accepted.append(row)
    return sorted(accepted,key=lambda r:r['publishedDate']),rejected


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-dir',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    key=os.environ.get('OPENROUTER_API_KEY','')
    if not key:p.error('OPENROUTER_API_KEY missing')
    args.output.mkdir(parents=True,exist_ok=False)
    report=json.loads(args.baseline.read_text())
    labels, failures, coverage = [], [], []
    for path in sorted(args.source_dir.glob('*-sources.json')):
        pair=json.loads(path.read_text());symbol=pair['symbol']
        end=date.fromisoformat(pair['event_date']);start=end-timedelta(days=2)
        try:
            raw=[];complete=False
            for page in range(3):
                batch=market_data.fmp('news/stock',symbols=symbol,**{'from':str(start),'to':str(end),'page':page,'limit':100},allow_empty=True)
                raw.extend(batch)
                if len(batch)<100:complete=True;break
            news,rejected=filter_news(raw,symbol,start,end)
            audit={'symbol':symbol,'from':str(start),'to':str(end),'raw_count':len(raw),
                   'accepted_count':len(news),'rejections':rejected,'pagination_complete':complete,
                   'observed_at':datetime.now(timezone.utc).isoformat(),
                   'historical_availability_verified':False}
            coverage.append(audit)
            (args.output/(symbol+'-news.json')).write_text(json.dumps({'audit':audit,'raw':raw,'accepted':news},indent=2))
            if not complete or not news:
                failures.append({'symbol':symbol,'reason':'Incomplete or empty news window'});continue
            # Publication dates end on the event day, strictly before baseline next-session entry.
            pair['news']=news
            label=annotate(pair,os.environ.get('OPENROUTER_MODEL_REVIEW') or 'openai/gpt-4o',key)
            (args.output/(symbol+'-label.json')).write_text(json.dumps(label,indent=2,ensure_ascii=False))
            labels.append(label)
            print(symbol,'news assessment completed',len(news),'articles',flush=True)
        except (market_data.ProviderError, ValueError) as exc:
            failures.append({'symbol':symbol,'reason':str(exc)})
    result=summarize(labels,report)
    result['limitations']=[x for x in result['limitations'] if not x.startswith('News and independent')]
    result['limitations'] += ['News window is event date minus two calendar days through event day, not later developments.',
        'No exact historical availability timestamp or independently verified full news coverage.',
        'News excerpts and syndication can limit evidence; independent peer confirmation remains untested.',
        'Paired-call and news annotations are separate model calls; differences can include model variability.']
    result['news_coverage']=coverage;result['failures']=failures
    (args.output/'report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps({'events':len(labels),'failures':failures},indent=2))


if __name__=='__main__':main()
