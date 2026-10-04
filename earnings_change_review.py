"""Replay source-only annotation review before joining frozen price outcomes."""

import llm_transport
import argparse
import hashlib
import json
import os
from pathlib import Path
from earnings_change_study import annotate, summarize


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-dir',type=Path,required=True,help='Paired transcript source directory')
    p.add_argument('--labels-dir',type=Path,required=True,help='Initial labels and optional SYMBOL-news.json')
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    key=llm_transport.credential()
    if not key:p.error('local Hermes subscription missing')
    a.output.mkdir(parents=True,exist_ok=False)
    labels,failures=[],[]
    for path in sorted(a.labels_dir.glob('*-label.json')):
        candidate=json.loads(path.read_text());symbol=candidate['symbol']
        pair=json.loads((a.source_dir/(symbol+'-sources.json')).read_text())
        if candidate['event_date']!=pair['event_date']:
            raise ValueError('Label/source event mismatch')
        news=a.labels_dir/(symbol+'-news.json')
        if news.exists():pair['news']=json.loads(news.read_text())['accepted']
        try:
            label=annotate(pair,llm_transport.MODEL,key,candidate)
            label['previous_label_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            (a.output/path.name).write_text(json.dumps(label,indent=2,ensure_ascii=False))
            labels.append(label)
        except ValueError as exc:
            failures.append({'symbol':symbol,'reason':str(exc)})
    result=summarize(labels,json.loads(a.baseline.read_text()))
    initial=json.loads((a.labels_dir/'report.json').read_text())
    result['limitations']=initial['limitations']
    if 'news_coverage' in initial:result['news_coverage']=initial['news_coverage']
    result['failures']=failures
    result['review_protocol']='Second price-blind source review; initial labels retained. Human review incomplete.'
    (a.output/'report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print('Reviewed annotations:',len(labels),'Failures:',len(failures))


if __name__=='__main__':main()
