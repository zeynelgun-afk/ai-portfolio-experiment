"""Telegram delivery state for Scout's research watchlist."""
from datetime import date


def normalize(symbols):
    if not isinstance(symbols, list) or any(not isinstance(s, str) or not s for s in symbols):
        raise ValueError('Invalid watchlist symbols')
    return sorted(set(symbols))


def change_message(symbols, previous=None, as_of=None):
    current = normalize(symbols)
    previous = normalize(previous) if previous is not None else None
    if previous == current:
        return None
    stamp = as_of or date.today().isoformat()
    if previous is None:
        heading = '📋 AI Portföy — mevcut araştırma hisse havuzu'
        changes = 'İlk havuz bildirimi.'
    else:
        added = sorted(set(current) - set(previous))
        removed = sorted(set(previous) - set(current))
        heading = '🔄 AI Portföy — araştırma hisse havuzu değişti'
        changes = ('Yeni: ' + (', '.join(added) if added else 'yok') + '\n' +
                   'Çıkan: ' + (', '.join(removed) if removed else 'yok'))
    return (f'{heading} ({stamp})\n\n' + ' · '.join(current) + '\n\n' +
            f'{changes}\n\nBu bir araştırma havuzudur; tek başına alım kararı değildir.')


def delivered_state(symbols, as_of=None):
    return {'symbols': normalize(symbols), 'delivered_at': as_of or date.today().isoformat(),
            'delivery_status': 'delivered'}
