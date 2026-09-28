"""Independent candidate feeds; channel membership is measured, never model-assigned."""
from datetime import datetime, timezone
import re
import market_data


def symbols(rows):
    if not isinstance(rows,list) or not rows:
        raise market_data.ProviderError('Empty discovery feed')
    result=[]
    for row in rows:
        symbol=row.get('symbol','')
        if isinstance(symbol,str) and re.fullmatch(r'[A-Z][A-Z0-9.-]{0,9}',symbol):
            result.append({k:v for k,v in row.items() if k in
                {'symbol','companyName','name','sector','industry','changesPercentage','price','marketCap','transactionType','filingDate'}})
    if not result:
        raise market_data.ProviderError('No valid discovery symbols')
    return result


def no_backup():
    raise market_data.ProviderError('No equivalent backup for this discovery feed')


def collect(now=None):
    now=now or datetime.now(timezone.utc)
    def yahoo_screen(name):
        import yfinance
        return yfinance.screen(name,count=30).get('quotes',[])
    def industry_pool():
        rows=[]
        for sector in ('Technology','Industrials','Energy','Utilities'):
            pool=symbols(market_data.fmp('company-screener',sector=sector,country='US',
                                        isEtf=False,isFund=False,isActivelyTrading=True,limit=1000))
            # Rotate the covered slice every week, rather than always taking the first names.
            pool=sorted(pool,key=lambda r:r['symbol'])
            start=(int(now.strftime('%W'))*25)%len(pool)
            rows.extend((pool+pool)[start:start+25])
        return rows
    def insiders():
        rows=market_data.fmp('insider-trading/latest',limit=100)
        return [r for r in rows if str(r.get('transactionType','')).startswith('P-Purchase')]
    feeds={
      'momentum':(lambda:market_data.fmp('biggest-gainers')[:30],lambda:yahoo_screen('day_gainers')),
      'dislocation':(lambda:market_data.fmp('biggest-losers')[:30],lambda:yahoo_screen('day_losers')),
      'structural_universe':(industry_pool,no_backup),
      'insider_purchase':(insiders,no_backup),
    }
    channels={}; membership={}; failures=[]
    for name,(primary,backup) in feeds.items():
        try:
            rows,provider=market_data.select('*','discovery:'+name,primary,backup,symbols)
            channels[name]={'provider':provider,'rows':rows,'observed_at':now.isoformat()}
            for row in rows:
                membership.setdefault(row['symbol'],[]).append(name)
        except market_data.ProviderError:
            failures.append(name)
    if not membership:
        raise market_data.ProviderError('All discovery channels unavailable')
    return {'observed_at':now.isoformat(),'channels':channels,'membership':membership,
            'unavailable_channels':failures,
            'limits':'Feed membership is a candidate signal, not proof of undervaluation, a bottleneck or future returns.'}
