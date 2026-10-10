"""Report incomplete analyst evidence without treating quarantined records as valid signals."""
import json
import os

from notify_failure import notify


def classify(data):
    unavailable, partial = [], []
    for symbol, row in data.items():
        if symbol.startswith('_'):
            continue
        report = row.get('analyst_revisions', {})
        if (report.get('status') in ('unavailable', 'no_records') or
                report.get('estimates_status') != 'ok'):
            unavailable.append(symbol)
        elif report.get('status') != 'ok':
            partial.append(symbol)
    return unavailable, partial


def main():
    with open('weekly_data.json', encoding='utf-8') as source:
        unavailable, partial = classify(json.load(source))
    if partial:
        print('::warning::Analyst observations quarantined for: ' + ', '.join(partial))
        notify(message='⚠️ AI Portföy — analist verisi kısmen eksik: ' + ', '.join(partial) +
               '. Çelişkili sağlayıcı kayıtları karantinada; bunlardan revizyon sinyali veya işlem üretilmedi. ' +
               'Kaynak: https://github.com/zeynelgun-afk/ai-portfolio-experiment/actions/runs/' +
               os.environ['GITHUB_RUN_ID'])
    if unavailable:
        raise SystemExit('Analyst revision evidence unavailable: ' + ', '.join(unavailable))


if __name__ == '__main__':
    main()
