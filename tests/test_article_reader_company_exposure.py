import unittest
from unittest.mock import patch

import article_reader
import company_exposure
import theme_radar


class ArticleReaderTests(unittest.TestCase):
    def test_reads_json_ld_article_body_and_marks_full_text(self):
        paragraph = 'The company manufactures optical transceivers for data center customers. '
        body = '\n\n'.join([paragraph + f'Paragraph {i}.' for i in range(20)])
        page = ('<html><head><title>Supply chain</title><script type="application/ld+json">'
                + __import__('json').dumps({'@type': 'NewsArticle', 'articleBody': body})
                + '</script></head><body></body></html>')
        rows = article_reader.enrich_news([{'id': 'a1', 'url': 'https://news.example/story', 'text': 'short'}],
                                         fetcher=lambda _: page)
        self.assertEqual(rows[0]['content_read_status'], 'article_body_extracted')
        self.assertGreaterEqual(rows[0]['body_word_count'], 100)
        self.assertIn('optical transceivers', rows[0]['article_body_text'])
        self.assertNotIn('article_body_text', article_reader.strip_transient_bodies(rows)[0])

    def test_excerpt_only_when_body_is_not_accessible_or_short(self):
        rows = article_reader.enrich_news([
            {'url': 'https://news.example/a'}, {'url': 'https://news.example/b'}],
            fetcher=lambda url: '<html><body><p>Short content.</p></body></html>' if url.endswith('/a') else None)
        self.assertTrue(all(row['content_read_status'] != 'article_body_extracted' for row in rows))

    def test_fetcher_rejects_non_public_and_non_https_urls(self):
        with patch.object(article_reader.socket, 'getaddrinfo', return_value=[
                (None, None, None, None, ('127.0.0.1', 443))]):
            self.assertIsNone(article_reader.fetch_article('https://example.com/a'))
        self.assertIsNone(article_reader.fetch_article('http://example.com/a'))


class CompanyExposureTests(unittest.TestCase):
    def test_article_quote_gate_rejects_excerpt_and_invented_quotes(self):
        quote = 'The company supplies EML laser components for optical transceivers.'
        radar = {'news': [{'id': 'a1', 'content_read_status': 'provider_excerpt_only',
                           'article_body_text': quote}], 'leading_industries': [{'industry': 'Optical'}]}
        result = theme_radar.validate_theme_analysis({'themes': [{'name':'Optics','stance':'watch',
            'article_ids':['a1'],'industries':['Optical']}], 'company_exposures': [{
            'company_name': 'Example Inc', 'symbol': 'EXM', 'article_ids': ['a1'],
            'article_evidence_quote': quote}]}, radar)
        self.assertEqual(result['company_exposures'], [])
        radar['news'][0]['content_read_status'] = 'article_body_extracted'
        result = theme_radar.validate_theme_analysis({'themes': [{'name':'Optics','stance':'watch',
            'article_ids':['a1'],'industries':['Optical']}], 'company_exposures': [{
            'company_name': 'Example Inc', 'symbol': 'EXM', 'article_ids': ['a1'],
            'article_evidence_quote': 'Invented statement about products.'}]}, radar)
        self.assertEqual(result['company_exposures'], [])
        result = theme_radar.validate_theme_analysis({'themes': [{'name':'Optics','stance':'watch',
            'article_ids':['a1'],'industries':['Optical']}], 'company_exposures': [{
            'company_name': 'Example Inc', 'symbol': 'EXM', 'article_ids': ['a1'],
            'article_evidence_quote': quote}]}, radar)
        self.assertEqual(len(result['themes']), 1)
        self.assertEqual(len(result['company_exposures']), 1)

    def test_filing_evidence_resolves_exact_issuer_and_retains_sec_link(self):
        def fmp(endpoint, **kwargs):
            if endpoint == 'profile':
                return [{'companyName': 'Coherent Corp.', 'cik': '0000820318'}]
            if endpoint == 'sec-filings-search/symbol':
                return [{'formType': '10-K', 'filingDate': '2026-08-20',
                         'cik':'0000820318',
                         'finalLink': 'https://www.sec.gov/Archives/edgar/data/820318/000082031826000123/cohr-10k.htm'}]
            raise AssertionError(endpoint)
        report = {'business': 'Coherent supplies optical transceivers and EML lasers to datacom customers.'}
        claim = {'company_name': 'Coherent Corp.', 'symbol': 'COHR', 'component': 'EML lasers',
                 'product': 'optical transceivers', 'role': 'supplies components'}
        requested_year=[]
        def get_report(url):
            requested_year.append(url)
            return report
        evidence = company_exposure.issuer_filing_evidence(claim, fmp=fmp,
                    get_report=get_report,
                    get_submissions=lambda cik:{'filings':{'recent':{
                        'accessionNumber':['0000820318-26-000123'],'form':['10-K'],
                        'reportDate':['2025-06-30']}}})
        self.assertEqual(evidence['issuer_status'], 'filing_retrieved')
        self.assertEqual(evidence['filing_url'], 'https://www.sec.gov/Archives/edgar/data/820318/000082031826000123/cohr-10k.htm')
        self.assertEqual(evidence['filing_fiscal_year'],2025)
        self.assertEqual(evidence['filing_period_end'],'2025-06-30')
        self.assertEqual(requested_year,[evidence['filing_url']])
        self.assertTrue(evidence['filing_contexts'])
        quote = evidence['filing_contexts'][0]
        verified = company_exposure.validate_issuer_verifications([{
            'symbol': 'COHR', 'verification_status': 'verified',
            'filing_evidence_quote': quote, 'reason': 'Product/component role appears in filing.'}], [evidence])
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]['verification_status'], 'verified')
        rejected = company_exposure.validate_issuer_verifications([{
            'symbol': 'COHR', 'verification_status': 'verified',
            'filing_evidence_quote': 'A fabricated issuer filing claim of sufficient length.'}], [evidence])
        self.assertEqual(rejected, [])

    def test_filing_year_is_not_guessed_from_calendar_filing_date(self):
        def fmp(endpoint, **kwargs):
            if endpoint == 'profile': return [{'companyName':'Coherent Corp.','cik':'0000820318'}]
            if endpoint == 'sec-filings-search/symbol': return [{'formType':'10-K',
                'filingDate':'2026-08-20','finalLink':'https://www.sec.gov/Archives/edgar/data/820318/000082031826000123/form10k.htm'}]
            raise AssertionError(endpoint)
        result=company_exposure.issuer_filing_evidence({'company_name':'Coherent Corp.','symbol':'COHR'},
            fmp=fmp,get_submissions=lambda cik:{'filings':{'recent':{'accessionNumber':[], 'form':[], 'reportDate':[]}}})
        self.assertEqual(result['issuer_status'],'filing_period_unverified')

    def test_20f_is_verified_from_its_exact_sec_document_and_report_period(self):
        def fmp(endpoint, **kwargs):
            if endpoint == 'profile': return [{'companyName':'Example Ltd.','cik':'0000820318'}]
            if endpoint == 'sec-filings-search/symbol': return [{'formType':'20-F',
                'filingDate':'2026-08-20','finalLink':'https://www.sec.gov/Archives/edgar/data/820318/000082031826000123/report.htm'}]
            raise AssertionError(endpoint)
        requested=[]
        result=company_exposure.issuer_filing_evidence({'company_name':'Example Ltd.','symbol':'EXM'},fmp=fmp,
            get_submissions=lambda cik:{'filings':{'recent':{'accessionNumber':['0000820318-26-000123'],
                'form':['20-F'],'reportDate':['2025-12-31']}}},
            get_report=lambda url:requested.append(url) or '<html><p>Example makes optical transceivers and laser systems.</p></html>')
        self.assertEqual(result['issuer_status'],'filing_retrieved')
        self.assertEqual(result['filing_period_end'],'2025-12-31')
        self.assertEqual(requested,[result['filing_url']])

    def test_exposure_candidates_enter_research_inbox_only_when_verified(self):
        radar = {'candidates': [], 'news': []}
        lead = {'symbol': 'COHR', 'company_name': 'Coherent Corp.', 'theme': 'AI optics',
                'product': 'optical transceivers', 'component': 'EML', 'role': 'supplier',
                'article_ids': ['a1'], 'filing_url': 'https://www.sec.gov/filing',
                'verification_status': 'verified'}
        result = theme_radar.attach_company_exposures(radar, [lead, {**lead, 'symbol': 'LITE',
            'verification_status': 'partial'}])
        self.assertEqual([row['symbol'] for row in result['candidates']], ['COHR'])
        self.assertEqual(result['candidates'][0]['candidate_type'], 'verified_company_product_exposure')
        self.assertEqual(radar['candidates'], [])


if __name__ == '__main__':
    unittest.main()
