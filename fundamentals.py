"""Dated quarterly statements, whole-dataset failover and auditable derived metrics."""
from datetime import datetime, timezone, date
import math
import market_data

FIELDS = {
 'income': ('income-statement', {'revenue':'Total Revenue', 'grossProfit':'Gross Profit',
            'operatingIncome':'Operating Income', 'netIncome':'Net Income'}),
 'balance': ('balance-sheet-statement', {'totalDebt':'Total Debt',
             'cashAndCashEquivalents':'Cash And Cash Equivalents', 'totalStockholdersEquity':'Stockholders Equity'}),
 'cashflow': ('cash-flow-statement', {'operatingCashFlow':'Operating Cash Flow',
              'capitalExpenditure':'Capital Expenditure', 'freeCashFlow':'Free Cash Flow'}),
}


def finite(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def validate(rows, symbol, kind, now):
    if not isinstance(rows, list) or not rows:
        raise market_data.ProviderError('Financial statements unavailable')
    valid = []
    seen = set()
    for row in rows:
        if row.get('symbol') != symbol or row.get('period') not in {'Q1','Q2','Q3','Q4','quarter'}:
            raise market_data.ProviderError('Statement issuer or period mismatch')
        day = date.fromisoformat(row['date'][:10])
        if day > now.date():
            continue
        published = row.get('acceptedDate') or row.get('filingDate')
        if published and date.fromisoformat(published[:10]) > now.date():
            continue
        if day in seen:
            raise market_data.ProviderError('Duplicate statement period')
        seen.add(day)
        currency = row.get('reportedCurrency')
        if not currency or not any(finite(row.get(k)) for k in FIELDS[kind][1]):
            raise market_data.ProviderError('Statement currency or numeric data missing')
        valid.append({**{k: row[k] if finite(row.get(k)) else None for k in FIELDS[kind][1]},
                      'date': day.isoformat(), 'currency': currency,
                      'published_at': published, 'period': row['period']})
    if not valid:
        raise market_data.ProviderError('No available historical statement')
    valid.sort(key=lambda row: row['date'], reverse=True)
    if (now.date()-date.fromisoformat(valid[0]['date'])).days > 200:
        raise market_data.ProviderError('Latest quarterly statement is stale')
    return valid[:8]


def statements(symbol, kind, now):
    endpoint, mapping = FIELDS[kind]
    def primary():
        return market_data.fmp(endpoint, symbol=symbol, period='quarter', limit=8)
    def backup():
        import yfinance
        ticker = yfinance.Ticker(symbol)
        frame = getattr(ticker, {'income':'quarterly_income_stmt', 'balance':'quarterly_balance_sheet',
                                 'cashflow':'quarterly_cashflow'}[kind])
        currency = ticker.info.get('financialCurrency')
        rows=[]
        for stamp in frame.columns:
            row={'symbol':symbol,'date':str(stamp)[:10],'period':'quarter','reportedCurrency':currency}
            for key, label in mapping.items():
                value = frame.loc[label, stamp] if label in frame.index else None
                row[key] = float(value) if value is not None else None
            # Yahoo represents expenditure as an outflow; keep FMP's signed field,
            # but derive FCF only as OCF minus absolute expenditure if absent.
            # Yahoo sometimes appends an empty old-period column. It is missing
            # coverage, not a reason to discard otherwise valid current quarters.
            if any(finite(row.get(key)) for key in mapping):
                rows.append(row)
        return rows
    return market_data.select(symbol, 'statements:'+kind, primary, backup,
                              lambda rows: validate(rows, symbol, kind, now))


def collect(symbol, now=None):
    now = now or datetime.now(timezone.utc)
    result={'statements':{}, 'providers':{}, 'facts':{}, 'gaps':[],
            'collected_at':now.isoformat(), 'management_guidance':'unavailable',
            'filing_footnotes':'not ingested'}
    for kind in FIELDS:
        try:
            rows, provider = statements(symbol, kind, now)
            result['statements'][kind]=rows
            result['providers'][kind]=provider
        except market_data.ProviderError:
            result['gaps'].append(kind+' statements unavailable')
    def add(name, value, unit, row, kind, operands):
        if finite(value):
            result['facts'][name]={'value':round(value,6), 'unit':unit, 'as_of':row['date'],
                'published_at':row['published_at'], 'observed_at':now.isoformat(),
                'source':result['providers'][kind]+'/'+FIELDS[kind][0], 'operands':operands}
    for kind, rows in result['statements'].items():
        row=rows[0]
        names={'revenue':'quarter_revenue','grossProfit':'quarter_gross_profit',
               'operatingIncome':'quarter_operating_income','netIncome':'quarter_net_income',
               'totalDebt':'total_debt','cashAndCashEquivalents':'cash_equivalents',
               'totalStockholdersEquity':'shareholders_equity','operatingCashFlow':'quarter_operating_cash_flow',
               'capitalExpenditure':'quarter_capex','freeCashFlow':'quarter_free_cash_flow'}
        for key in FIELDS[kind][1]:
            add(names[key], row.get(key), row['currency'], row, kind, [key])
        if row['published_at'] is None:
            result['gaps'].append(kind+': publication timestamp unavailable; observed snapshot only')
        if kind == 'income' and finite(row.get('revenue')) and row['revenue'] > 0:
            for key, name in [('grossProfit','gross_margin_pct'),('operatingIncome','operating_margin_pct')]:
                if finite(row.get(key)):
                    add(name,100*row[key]/row['revenue'],'%',row,kind,[key,'revenue'])
            older=next((r for r in rows[1:] if 340 <= (date.fromisoformat(row['date'])-date.fromisoformat(r['date'])).days <= 390 and r['currency']==row['currency']),None)
            if older and finite(older.get('revenue')) and older['revenue'] > 0:
                add('revenue_yoy_pct',100*(row['revenue']/older['revenue']-1),'%',row,kind,['revenue@'+row['date'],'revenue@'+older['date']])
            else:
                result['gaps'].append('Comparable prior-year quarter unavailable')
        if kind == 'balance' and all(finite(row.get(k)) for k in ('totalDebt','cashAndCashEquivalents')):
            add('net_debt',row['totalDebt']-row['cashAndCashEquivalents'],row['currency'],row,kind,['totalDebt','cashAndCashEquivalents'])
    return result


MONITOR_METRICS = {'revenue_yoy_pct', 'gross_margin_pct', 'operating_margin_pct',
                   'quarter_operating_cash_flow', 'quarter_free_cash_flow', 'net_debt', 'total_debt'}


def measured_fact(condition, row, today):
    """A statement period is not its observation time; never treat missing/stale as healthy."""
    metric = condition.get('metric')
    if metric not in MONITOR_METRICS:
        return None
    packet = row.get('fundamental_research', {})
    try:
        observed = datetime.fromisoformat(packet['collected_at'])
        fact = packet['facts'][metric]
        period = date.fromisoformat(fact['as_of'])
        if observed.date() != today or (today-period).days not in range(201):
            return None
        if not finite(fact['value']) or not fact.get('source') or not fact.get('unit'):
            return None
        if condition.get('unit') != fact['unit']:
            return None
        return fact
    except (KeyError, TypeError, ValueError):
        return None
