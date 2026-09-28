"""Report degraded providers once per workflow, without interrupting valid failover."""
import json
from pathlib import Path
from notify_failure import notify


def summary(events):
    affected = sorted({(e['symbol'], e['dataset'], e['provider']) for e in events if e['provider'] != 'FMP'})
    if not affected:
        return None
    lines = ['⚠️ AI Portföy — veri sağlayıcı durumu',
             'FMP bazı verileri sağlayamadı. Yedek kullanılan ve eksik kalan alanlar:']
    lines += [f'{symbol} / {dataset}: {provider}' for symbol,dataset,provider in affected[:25]]
    if len(affected)>25:
        lines.append(f'Ek etkilenen veri kümesi: {len(affected)-25}')
    lines.append('yfinance yalnızca başarısız veri isteğinin yerine kullanılır. Eksik veri uydurulmaz.')
    return '\n'.join(lines)


def main():
    path=Path(__file__).resolve().parent/'output/provider-events.jsonl'
    if not path.exists():
        return
    text=summary([json.loads(line) for line in path.read_text().splitlines() if line.strip()])
    if text:
        notify(message=text)
    else:
        print('Provider health: FMP served all requested datasets; backup idle')


if __name__=='__main__':main()
