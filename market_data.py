"""FMP-first data access. yfinance is lazy, per-dataset failover, never a second vote."""
from datetime import datetime, timedelta, timezone, date
import json
import math
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo

import pandas as pd
import pandas_market_calendars as calendars
import requests

from market_time import session, market_open, recent

BASE = Path(__file__).resolve().parent
EVENTS = []


class ProviderError(RuntimeError):
    pass


def fmp(endpoint, **params):
    key = os.environ.get('FMP_API_KEY', '').strip()
    if not key:
        raise ProviderError('FMP key unavailable')
    for attempt in range(2):
        try:
            response = requests.get('https://financialmodelingprep.com/stable/' + endpoint,
                                    params={**params, 'apikey': key}, timeout=15)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == 0:
                    time.sleep(1)
                    continue
            if response.status_code != 200:
                raise ProviderError(f'FMP HTTP {response.status_code}')
            payload = response.json()
            if not isinstance(payload, list) or not payload:
                raise ProviderError('FMP empty or invalid response')
            return payload
        except ProviderError:
            raise
        except (requests.RequestException, ValueError):
            if attempt == 0:
                time.sleep(1)
                continue
            raise ProviderError('FMP transport or JSON failure') from None
    raise ProviderError('FMP unavailable')


def event(symbol, dataset, provider, reason=None):
    row = {'symbol': symbol, 'dataset': dataset, 'provider': provider,
           'observed_at': datetime.now(timezone.utc).isoformat()}
    if reason:
        row['reason'] = reason
    EVENTS.append(row)
    if os.environ.get('GITHUB_ACTIONS') == 'true' or os.environ.get('PROVIDER_EVENTS_PATH'):
        path = Path(os.environ.get('PROVIDER_EVENTS_PATH', str(BASE/'output/provider-events.jsonl')))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a') as handle:
            handle.write(json.dumps(row) + '\n')
    if provider != 'FMP':
        print(f'Provider failover: {symbol} / {dataset} -> {provider} ({reason})')


def select(symbol, dataset, primary, backup, validate=lambda value: value):
    try:
        result = validate(primary())
        event(symbol, dataset, 'FMP')
        return result, 'FMP'
    except Exception as error:
        # Provider URLs may contain API keys: never include arbitrary exceptions.
        reason = str(error) if isinstance(error, ProviderError) else 'FMP data validation failed'
    try:
        result = validate(backup())
        event(symbol, dataset, 'yfinance', reason)
        return result, 'yfinance'
    except Exception:
        event(symbol, dataset, 'unavailable', reason)
        raise ProviderError(f'Both providers unavailable for {symbol}/{dataset}') from None


def last_closed(now):
    for offset in range(14):
        day = now.astimezone(ZoneInfo('America/New_York')).date() - timedelta(days=offset)
        bounds = session(day)
        if bounds and bounds[1] <= now:
            return day
    raise ProviderError('No completed session')


def validate_history(frame, interval, now):
    if frame is None or frame.empty or not {'Close', 'Volume'} <= set(frame.columns):
        raise ProviderError('Missing price/volume series')
    frame = frame.copy().sort_index()
    if frame.index.has_duplicates:
        raise ProviderError('Duplicate market timestamps')
    for field in ('Close', 'Volume'):
        values = pd.to_numeric(frame[field], errors='coerce')
        if values.isna().any() or not values.map(lambda n: float('-inf') < n < float('inf')).all():
            raise ProviderError('Invalid market values')
        if (values <= 0).any() if field == 'Close' else (values < 0).any():
            raise ProviderError('Invalid price/volume range')
        frame[field] = values
    if interval == '1d':
        expected = last_closed(now)
        valid_days = set(calendars.get_calendar('NYSE').valid_days(
            start_date=frame.index.min().date(), end_date=expected).date)
        frame = frame.loc[[t.date() in valid_days for t in frame.index]]
        if frame.empty or frame.index[-1].date() != expected:
            raise ProviderError('Stale daily series')
        frame.index = pd.DatetimeIndex([t.date() for t in frame.index])
    else:
        if frame.index.tz is None:
            raise ProviderError('Intraday timezone missing')
        frame.index = frame.index.tz_convert('UTC')
        frame = frame.loc[[bool(session(t.date()) and session(t.date())[0] <= t < session(t.date())[1]) for t in frame.index]]
        if frame.empty or frame.index[-1].to_pydatetime() > now:
            raise ProviderError('Missing or future session bars')
        if not market_open(now) and frame.index[-1].date() != last_closed(now):
            raise ProviderError('Stale last-session intraday series')
        if market_open(now) and not recent(frame.index[-1].isoformat(), now):
            raise ProviderError('Stale intraday series')
        # Match the existing one-session volume calculation, never sum multiple days.
        frame = frame.loc[frame.index.date == frame.index[-1].date()]
    return frame


def history(symbol, period='2y', interval='1d', now=None):
    now = now or datetime.now(timezone.utc)
    days = {'2y': 740, '120d': 180, '10d': 25, '5d': 15, '1d': 10}.get(period)
    if days is None or interval not in {'1d', '5m'}:
        raise ValueError('Unsupported measured history request')
    def primary():
        endpoint = 'historical-price-eod/full' if interval == '1d' else 'historical-chart/5min'
        rows = fmp(endpoint, symbol=symbol, **{'from': (now.date()-timedelta(days=days)).isoformat(), 'to': now.date().isoformat()})
        if any(row.get('symbol', symbol) != symbol for row in rows):
            raise ProviderError('FMP issuer mismatch')
        frame = pd.DataFrame(rows).rename(columns={k:k.title() for k in ('open','high','low','close','volume')})
        index = pd.DatetimeIndex(pd.to_datetime(frame.pop('date'), errors='raise'))
        if interval == '5m':
            index = index.tz_localize('America/New_York') if index.tz is None else index
        frame.index = index
        return frame
    def backup():
        import yfinance
        return yfinance.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False, prepost=False)
    frame, provider = select(symbol, 'history:' + interval, primary, backup,
                             lambda data: validate_history(data, interval, now))
    frame.attrs['provider'] = provider
    return frame


def download(tickers, period='10d', interval='1d', **kwargs):
    symbols = tickers.split() if isinstance(tickers, str) else list(tickers)
    frames = {}
    providers = {}
    for symbol in symbols:
        try:
            frame = history(symbol, period, interval)
            providers[symbol] = frame.attrs['provider']
            frames[symbol] = frame[['Close', 'Volume']]
        except ProviderError:
            if interval != '5m':
                raise
    if not frames:
        raise ProviderError('No measured series available')
    result = pd.concat(frames, axis=1).swaplevel(0,1,axis=1).sort_index(axis=1)
    result.attrs['providers'] = providers
    return result


def news(symbol):
    def primary():
        rows = fmp('news/stock', symbols=symbol, limit=10)
        if any(r.get('symbol') != symbol for r in rows):
            raise ProviderError('FMP news issuer mismatch')
        return rows
    def backup():
        import yfinance
        rows = []
        for item in yfinance.Ticker(symbol).news or []:
            c = item.get('content') or item
            rows.append({'symbol':symbol, 'title':c.get('title'), 'text':c.get('summary',''),
                         'publishedDate':c.get('pubDate') or c.get('displayTime'),
                         'url':(c.get('canonicalUrl') or {}).get('url') or item.get('link')})
        return rows
    def valid(rows):
        if not rows or any(not r.get('title') or not r.get('publishedDate') for r in rows):
            raise ProviderError('Missing news title/timestamp')
        for row in rows:
            original = row['publishedDate']
            pd.Timestamp(original)  # Reject malformed publication stamps.
            row['sourcePublishedDate'] = original
            row['publishedDate'] = str(original).replace('T', ' ')[:19]
        return rows
    rows, provider = select(symbol, 'news', primary, backup, valid)
    return rows, provider


class Ticker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.providers = {}

    def history(self, period='2y', **kwargs):
        result = history(self.symbol, period, kwargs.get('interval','1d'))
        self.providers['history'] = result.attrs['provider']
        return result

    @property
    def calendar(self):
        def primary():
            rows=fmp('earnings',symbol=self.symbol,limit=100)
            if any(r.get('symbol',self.symbol)!=self.symbol for r in rows):
                raise ProviderError('FMP earnings issuer mismatch')
            upcoming=sorted(date.fromisoformat(r['date'][:10]) for r in rows if r.get('date') and r['date'][:10]>=date.today().isoformat())
            if not upcoming:raise ProviderError('FMP upcoming earnings unavailable')
            return {'Earnings Date':[upcoming[0]]}
        def backup():
            import yfinance
            return yfinance.Ticker(self.symbol).calendar
        def valid(value):
            if not isinstance(value,dict) or not value.get('Earnings Date'):
                raise ProviderError('Earnings date unavailable')
            first = value['Earnings Date'][0]
            day = date.fromisoformat(str(first)[:10])
            if day < date.today():
                raise ProviderError('Stale earnings calendar')
            return value
        result,provider=select(self.symbol,'earnings',primary,backup,valid)
        self.providers['earnings']=provider
        return result

    @property
    def info(self):
        def primary():
            ratios=fmp('ratios-ttm',symbol=self.symbol)[0]
            quote=fmp('quote',symbol=self.symbol)[0]
            if ratios.get('symbol')!=self.symbol or quote.get('symbol')!=self.symbol:
                raise ProviderError('FMP fundamentals issuer mismatch')
            return {'trailingPE':ratios.get('priceToEarningsRatioTTM'),
                    'marketCap':quote.get('marketCap'), 'forwardPE':None}
        def backup():
            import yfinance
            return yfinance.Ticker(self.symbol).info
        def valid(value):
            cap = value.get('marketCap') if isinstance(value, dict) else None
            if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not math.isfinite(cap) or cap <= 0:
                raise ProviderError('Fundamental snapshot unavailable')
            return value
        result,provider=select(self.symbol,'fundamentals',primary,backup,valid)
        self.providers['fundamentals']=provider
        return result

    @property
    def news(self):
        rows,provider=news(self.symbol)
        self.providers['news']=provider
        return rows
