"""Resolve article-named companies and gather dated issuer filing evidence."""
from html.parser import HTMLParser
from datetime import date, timedelta
import os
import re

import requests

import market_data

SEC_ROOT = 'https://www.sec.gov'
MAX_EXPOSURES = 5
COMPONENT_TERMS = ('optical', 'transceiver', 'photonics', 'laser', 'EML',
                   'indium phosphide', 'silicon photonics', 'digital signal processor',
                   'printed circuit board', 'mSAP', 'data center', 'datacom', 'optical module')


def _normal_name(value):
    value = re.sub(r'[^a-z0-9 ]', ' ', str(value or '').lower())
    words = [word for word in value.split() if word not in {
        'inc', 'incorporated', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited',
        'plc', 'holdings', 'holding', 'the'}]
    return ' '.join(words)


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocked = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript', 'svg'}:
            self.blocked += 1
        elif not self.blocked and tag in {'p', 'div', 'tr', 'li', 'h1', 'h2', 'h3', 'br'}:
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript', 'svg'} and self.blocked:
            self.blocked -= 1
        elif not self.blocked and tag in {'p', 'div', 'tr', 'li', 'h1', 'h2', 'h3'}:
            self.parts.append('\n')
    def handle_data(self, data):
        if not self.blocked:
            self.parts.append(data)


def _filing_text(html):
    parser = _TextParser()
    parser.feed(html)
    text = re.sub(r'[ \t]+', ' ', ''.join(parser.parts))
    return re.sub(r'\n\s*\n+', '\n', text)


def _filing_context(text, claim):
    terms = set(COMPONENT_TERMS)
    for value in (claim.get('component'), claim.get('product'), claim.get('role')):
        terms.update(word.lower() for word in re.findall(r'[A-Za-z][A-Za-z0-9-]{3,}', str(value or '')))
    matches = []
    for term in sorted(terms, key=len, reverse=True):
        for match in re.finditer(re.escape(term), text, flags=re.I):
            start, end = max(0, match.start()-350), min(len(text), match.end()+550)
            context = ' '.join(text[start:end].split())
            if context and all(abs(match.start()-prior[0]) > 300 for prior in matches):
                matches.append((match.start(), context))
            if len(matches) >= 8:
                break
        if len(matches) >= 8:
            break
    return [snippet for _, snippet in sorted(matches)]


def _matching_symbol(company_name, proposed_symbol=None, fmp=market_data.fmp):
    rows = []
    if isinstance(proposed_symbol, str) and proposed_symbol.strip():
        rows = fmp('profile', symbol=proposed_symbol.strip().upper(), allow_empty=True)
    if rows:
        name = rows[0].get('companyName') or rows[0].get('name')
        if _normal_name(name) == _normal_name(company_name):
            return proposed_symbol.strip().upper(), rows[0]
    matches = fmp('search-name', query=company_name, limit=10, allow_empty=True)
    for item in matches:
        symbol = item.get('symbol')
        name = item.get('companyName') or item.get('name')
        if not isinstance(symbol, str) or _normal_name(name) != _normal_name(company_name):
            continue
        profiles = fmp('profile', symbol=symbol, allow_empty=True)
        if profiles and _normal_name(profiles[0].get('companyName')) == _normal_name(company_name):
            return symbol, profiles[0]
    return None, None


def issuer_filing_evidence(claim, *, fmp=market_data.fmp, get_report=None):
    """Return dated annual issuer-report evidence linked to its official SEC filing."""
    company_name = str(claim.get('company_name') or '').strip()
    if not company_name:
        return {**claim, 'issuer_status': 'company_name_missing'}
    try:
        symbol, profile = _matching_symbol(company_name, claim.get('symbol'), fmp)
        cik = str((profile or {}).get('cik') or '').strip()
        if not symbol or not cik.isdigit():
            return {**claim, 'issuer_status': 'issuer_identity_unverified'}
        start = (date.today() - timedelta(days=550)).isoformat()
        end = date.today().isoformat()
        filings = fmp('sec-filings-search/symbol', symbol=symbol,
            **{'from': start, 'to': end, 'page': 0, 'limit': 100}, allow_empty=True)
        eligible = [row for row in filings if row.get('formType') in {'10-K', '20-F', '40-F'}
                    and row.get('filingDate') and (row.get('finalLink') or row.get('link'))]
        if not eligible:
            return {**claim, 'symbol': symbol, 'issuer_status': 'no_recent_periodic_filing'}
        filing = max(eligible, key=lambda row: row['filingDate'])
        filing_date = str(filing['filingDate'])[:10]
        filing_url = filing.get('finalLink') or filing.get('link')
        year_match = re.search(r'(?:19|20)\d{2}', filing_url.rsplit('/', 1)[-1])
        report_year = int(year_match.group()) if year_match else int(filing_date[:4])
        if get_report is None:
            key = os.environ.get('FMP_API_KEY', '').strip()
            if not key:
                return {**claim, 'symbol': symbol, 'issuer_status': 'filing_provider_key_unavailable'}
            response = requests.get('https://financialmodelingprep.com/stable/financial-reports-json',
                params={'symbol': symbol, 'year': report_year, 'period': 'FY', 'apikey': key}, timeout=30)
            response.raise_for_status()
            report = response.json()
        else:
            report = get_report(symbol, report_year, 'FY')
        if not isinstance(report, dict):
            return {**claim, 'symbol': symbol, 'issuer_status': 'filing_content_unavailable'}
        text = _filing_text(__import__('json').dumps(report, ensure_ascii=False))
        contexts = _filing_context(text, claim)
        return {**claim, 'symbol': symbol, 'issuer_status': 'filing_retrieved',
            'issuer_name': profile.get('companyName'), 'cik': cik.zfill(10), 'filing_form': filing.get('formType'),
            'filing_date': filing_date, 'filing_url': filing_url,
            'filing_data_source': 'FMP extracted SEC annual filing',
            'filing_contexts': contexts, 'filing_has_relevant_context': bool(contexts)}
    except Exception:
        return {**claim, 'issuer_status': 'filing_unavailable'}


def collect_issuer_evidence(claims):
    results = []
    seen = set()
    for claim in claims:
        if len(results) >= MAX_EXPOSURES:
            break
        identity = (_normal_name(claim.get('company_name')), claim.get('theme'))
        if identity in seen:
            continue
        seen.add(identity)
        results.append(issuer_filing_evidence(claim))
    return results


def validate_issuer_verifications(rows, evidence):
    """Only retain model verification when its quoted passage exists in the SEC filing text."""
    by_symbol = {row.get('symbol'): row for row in evidence if row.get('symbol')}
    output = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or row.get('verification_status') not in {
                'verified', 'partial', 'not_supported', 'uncertain'}:
            continue
        source = by_symbol.get(row.get('symbol'))
        if not source or source.get('issuer_status') != 'filing_retrieved':
            continue
        quote = ' '.join(str(row.get('filing_evidence_quote') or '').split())
        contexts = [' '.join(str(item).split()) for item in source.get('filing_contexts', [])]
        if row['verification_status'] == 'verified' and (len(quote) < 40 or not any(quote in item for item in contexts)):
            continue
        output.append({**source, **row, 'company_name': source.get('issuer_name'),
            'filing_form': source['filing_form'], 'filing_date': source['filing_date'],
            'filing_url': source['filing_url'], 'issuer_source': 'SEC EDGAR company filing',
            'verification_status': row['verification_status']})
    return output
