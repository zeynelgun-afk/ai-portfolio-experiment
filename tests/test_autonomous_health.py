"""Recovery contracts keep bad evidence rejected and paper execution autonomous."""
import json
import subprocess
from unittest.mock import patch
import pytest
import llm_transport
import reassess
import reviewers
import detector
from claim_evidence import documents


def test_invalid_structured_response_retries_same_subscription_bounded():
    error = llm_transport.InferenceError('Invalid structured response', retryable=True)
    with patch('llm_transport.complete', side_effect=[error, '{"findings":[],"clean":true}']) as call:
        with patch.object(reassess, 'SLEEP') as sleep:
            payload, status = reassess._call_llm('ignored', 'system', 'evidence', 'local',
                response_schema=reviewers.AUDITOR_RESPONSE_SCHEMA, response_validator=reviewers.validate_audit)
    assert status == 'ok' and payload['clean']
    assert call.call_count == 2
    sleep.assert_called_once()
    assert all(c.kwargs['response_schema'] == reviewers.AUDITOR_RESPONSE_SCHEMA for c in call.call_args_list)
    correction = call.call_args_list[-1].args[0][-1]['content']
    assert 'Escape quotes' in correction and 'evidence' in correction


def test_persistent_bad_output_stops_without_decision():
    with patch('llm_transport.complete', side_effect=llm_transport.InferenceError('Invalid structured response', retryable=True)) as call:
        result = reassess._call_llm('ignored', 'system', 'evidence', 'local', sleep=lambda _: None)
    assert result == (None, 'unparseable')
    assert call.call_count == reassess.MAX_ATTEMPTS



def test_auditor_cannot_call_conflicting_report_clean():
    with pytest.raises(ValueError):
        reviewers.validate_audit({'findings': [{'pattern': 'phantom_rule'}], 'clean': True})


def news():
    return {'symbol': 'MU', 'url': 'https://example.org/report',
            'publishedDate': '2026-10-09 10:00:00', 'title': 'Issuer report', 'text': ''}


def test_extracted_body_is_citable_with_correct_provenance():
    item = dict(news(), article_body_text='Measured issuer revenue increased according to the published report. '*5,
                content_read_status='article_body_extracted')
    source = next(iter(documents('MU', [item]).values()))
    assert source['text'] == item['article_body_text'].strip()
    assert 'extracted article body' in source['scope']
    assert not documents('MU', [dict(item, symbol='AMD')])


def test_missing_article_remains_unassessed_not_clean():
    with patch('article_reader.enrich_news', return_value=[news()]) as recover, patch('reassess.call_llm') as model:
        outcome, detail = detector.check_news_shock('MU', 'Demand thesis', [news()])
    assert outcome is None and 'unavailable' in detail
    model.assert_not_called()
    recover.assert_called_once()


def test_valuation_checkpoint_commits_before_model_failure_with_ignored_telegram(tmp_path):
    from pathlib import Path
    import yaml
    workflow = yaml.safe_load((Path(__file__).resolve().parents[1]/'.github/workflows/weekly.yml').read_text())
    steps = workflow['jobs']['round']['steps']
    checkpoint = next(s['run'] for s in steps if s.get('name') == 'Persist valuation before model-dependent research')
    remote = tmp_path/'remote.git'
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    work = tmp_path/'work'; work.mkdir()
    def git(*args):
        return subprocess.run(['git', *args], cwd=work, check=True, capture_output=True, text=True)
    git('init', '-b', 'main');git('config', 'user.name', 'test');git('config', 'user.email', 'test@example.org')
    (work/'.gitignore').write_text('telegram.txt\n')
    for file in ('REPORT.md', 'history.csv', 'portfolio.json'):
        (work/file).write_text('previous\n')
    git('add', '.');git('commit', '-m', 'initial');git('remote', 'add', 'origin', str(remote));git('push', '-u', 'origin', 'main')
    for file in ('REPORT.md', 'history.csv', 'portfolio.json', 'telegram.txt'):
        (work/file).write_text('current\n')
    subprocess.run(['bash', '-e', '-c', checkpoint], cwd=work, check=True, capture_output=True)
    assert git('show', 'HEAD:REPORT.md').stdout == 'current\n'
    assert git('ls-remote', 'origin', 'refs/heads/main').stdout.split()[0] == git('rev-parse', 'HEAD').stdout.strip()
    assert not git('ls-files', 'telegram.txt').stdout


def test_auditor_selects_code_owned_quote_without_transcribing_quotes():
    prompt='The source states "a quoted claim" with a conflicting account.'
    spans, annotated=reviewers.evidence_spans(prompt)
    assert spans['E1']==prompt and '[E1]' in annotated
    payload={'findings':[{'pattern':'unsourced_reasoning','where':'round',
        'evidence_id':'E1','severity':'medium','why':'The claim lacks supporting evidence.'}], 'clean':False}
    with patch('reviewers.reassess.call_llm',return_value=(payload,'ok')) as call:
        result=reviewers.run_auditor('local',prompt,'local')
    assert result[0]['evidence']==prompt
    assert call.call_args.kwargs['response_schema']['schema']['properties']['findings']['items']['properties']['evidence_id']['enum']==['E1']
    payload['findings'][0]['evidence_id']='invented'
    with patch('reviewers.reassess.call_llm',return_value=(payload,'ok')):
        assert reviewers.run_auditor('local',prompt,'local') is None


def test_scout_corrects_out_of_universe_selection_before_writing_any_state():
    import scout
    symbols=['T'+chr(65+i) for i in range(15)]
    discovery={'membership':{s:['structural_universe'] for s in symbols},'channels':{}}
    answers=[json.dumps({'symbols':symbols[:-1]+['FAKE']}),json.dumps({'symbols':symbols})]
    with patch('llm_transport.complete',side_effect=answers) as infer:
        with patch('scout.write_json') as write:
            assert scout.select_symbols(discovery,'local')==symbols
    assert infer.call_count==2
    assert 'company without discovery evidence' in infer.call_args_list[-1].args[0][-1]['content']
    write.assert_not_called()


def test_scout_persistent_invalid_selection_never_becomes_watchlist():
    import scout
    symbols=['T'+chr(65+i) for i in range(15)]
    with patch('llm_transport.complete',return_value=json.dumps({'symbols':['FAKE']*15})) as infer:
        with patch('scout.write_json') as write:
            with pytest.raises(RuntimeError,match='rejected'):
                scout.select_symbols({'membership':dict.fromkeys(symbols,[])},'local')
    assert infer.call_count==reassess.MAX_ATTEMPTS
    write.assert_not_called()
