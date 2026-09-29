"""Resolve article-named companies and gather dated issuer filing evidence."""
from html.parser import HTMLParser
from datetime import date, timedelta
import os
import re

import requests

import market_data

SEC_ROOT = 'https://www.sec.gov'
MAX_EXPOSURES = 5
MAX_FILING_BYTES = 20_000_000
ANNUAL_FORMS = {'10-K', '20-F', '40-F'}
COMPONENT_TERMS = ('optical', 'transceiver', 'photonics', 'laser', 'EML',
                   'indium phosphide', 'silicon photonics', 'digital signal processor',
                   'printed circuit board', 'mSAP', 'data center', 'datacom', 'optical module')
SEC_USER_AGENT_PREFIX = 'AI-Portfolio-Experiment research'


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


def _sec_report_period(cik, filing, get_submissions=None):
    """Resolve the fiscal period from the exact SEC accession, never filing year."""
    links = [filing.get('link'), filing.get('finalLink')]
    accession = None
    for link in links:
        match = re.search(r'/Archives/edgar/data/\d+/(\d{18})(?:/|$)', str(link or ''))
        if match:
            accession = match.group(1)
            break
    if not accession:
        return None
    payload = (get_submissions(cik) if get_submissions else requests.get(
        f'{SEC_ROOT}/submissions/CIK{str(cik).zfill(10)}.json',
        headers=_sec_headers(), timeout=20
    ).json())
    recent = payload.get('filings', {}).get('recent', {}) if isinstance(payload, dict) else {}
    accessions = recent.get('accessionNumber', [])
    for index, value in enumerate(accessions):
        if str(value).replace('-', '') != accession:
            continue
        forms = recent.get('form', [])
        dates = recent.get('reportDate', [])
        form = forms[index] if index < len(forms) else None
        report_date = dates[index] if index < len(dates) else None
        if form not in ANNUAL_FORMS or not isinstance(report_date, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', report_date):
            return None
        return {'accession': str(value), 'form': form, 'report_date': report_date,
                'fiscal_year': int(report_date[:4])}
    return None


def _sec_headers():
    email = os.environ.get('SEC_CONTACT_EMAIL', '').strip()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise RuntimeError('SEC_CONTACT_EMAIL is not configured')
    return {'User-Agent': f'{SEC_USER_AGENT_PREFIX} {email}',
            'Accept-Encoding': 'gzip, deflate'}


def _has_sec_contact():
    return bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',
                             os.environ.get('SEC_CONTACT_EMAIL', '').strip()))


def _download_sec_filing(url):
    """Read a bounded primary filing document from SEC EDGAR only."""
    from urllib.parse import urlsplit
    parts = urlsplit(str(url or ''))
    if (parts.scheme != 'https' or parts.hostname not in {'www.sec.gov', 'sec.gov'} or
            not parts.path.startswith('/Archives/edgar/data/')):
        raise ValueError('Filing URL is not an SEC EDGAR archive document')
    with requests.get(url, headers={**_sec_headers(),
            'Accept': 'text/html,application/xhtml+xml,application/xml'},
            timeout=30, stream=True, allow_redirects=False) as response:
        if response.is_redirect:
            raise ValueError('SEC filing URL unexpectedly redirected')
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type and not any(kind in content_type for kind in ('html', 'xml', 'text/plain')):
            raise ValueError('SEC filing is not a readable document')
        chunks=[]; size=0
        for chunk in response.iter_content(131072):
            if not chunk: continue
            size += len(chunk)
            if size > MAX_FILING_BYTES:
                raise ValueError('SEC filing exceeded the bounded document size')
            chunks.append(chunk)
        return b''.join(chunks).decode(response.encoding or 'utf-8', errors='replace')


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


def issuer_filing_evidence(claim, *, fmp=market_data.fmp, get_report=None, get_submissions=None):
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
        eligible = [row for row in filings if row.get('formType') in ANNUAL_FORMS
                    and row.get('filingDate') and (row.get('finalLink') or row.get('link'))]
        if not eligible:
            return {**claim, 'symbol': symbol, 'issuer_status': 'no_recent_periodic_filing'}
        filing = max(eligible, key=lambda row: row['filingDate'])
        filing_date = str(filing['filingDate'])[:10]
        filing_url = filing.get('finalLink') or filing.get('link')
        filing_cik = str(filing.get('cik') or '').strip()
        if filing_cik.isdigit() and filing_cik.zfill(10) != cik.zfill(10):
            return {**claim, 'symbol': symbol, 'issuer_status': 'filing_issuer_mismatch'}
        if get_submissions is None and not _has_sec_contact():
            return {**claim, 'symbol': symbol, 'issuer_status': 'sec_contact_unconfigured'}
        period = _sec_report_period(cik, filing, get_submissions)
        if not period or period['form'] != filing.get('formType'):
            return {**claim, 'symbol': symbol, 'issuer_status': 'filing_period_unverified'}
        report_year = period['fiscal_year']
        if get_report is None and not _has_sec_contact():
            return {**claim, 'symbol': symbol, 'issuer_status': 'sec_contact_unconfigured'}
        report = get_report(filing_url) if get_report else _download_sec_filing(filing_url)
        if not isinstance(report, (str, dict)):
            return {**claim, 'symbol': symbol, 'issuer_status': 'filing_content_unavailable'}
        text = _filing_text(report if isinstance(report, str) else
                            __import__('json').dumps(report, ensure_ascii=False))
        contexts = _filing_context(text, claim)
        return {**claim, 'symbol': symbol, 'issuer_status': 'filing_retrieved',
            'issuer_name': profile.get('companyName'), 'cik': cik.zfill(10), 'filing_form': filing.get('formType'),
            'filing_date': filing_date, 'filing_url': filing_url,
            'filing_accession': period['accession'], 'filing_period_end': period['report_date'],
            'filing_fiscal_year': report_year,
            'filing_data_source': 'Exact SEC EDGAR primary filing document',
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
