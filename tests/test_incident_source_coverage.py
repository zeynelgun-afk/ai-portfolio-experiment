"""The reviewer must receive the same bounded article evidence as the proposer."""
import json
from unittest.mock import patch
import pytest
import claim_evidence
import llm_context
import reassess


def data():
    return {'MU': {'source_documents': {
        f'news:{i}': {'symbol': 'MU', 'published_at': f'2026-10-{i:02}',
                     'title': f'article-{i}', 'text': f'Exact article {i}. ' * 200,
                     'url': f'https://example.test/{i}', 'scope': 'fixture'}
        for i in range(1, 10)}}}


def test_proposer_and_reviewer_have_identical_article_excerpts():
    rows = data()
    expected = llm_context.research_view(rows)['MU']['source_documents']
    def inspect(*args, **kwargs):
        actual = json.loads(args[2])['sources']
        assert {s['title']: s['text'] for s in actual.values()} == {
            s['title']: s['text'] for s in expected.values()}
        return None, 'offline_stop'
    with patch.object(reassess, 'call_llm', side_effect=inspect):
        with pytest.raises(ValueError, match='offline_stop'):
            claim_evidence.semantic_review({'reasoning': 'Fixture'}, rows, {}, '', '')


def test_candidate_citation_outside_bounded_bundle_fails_before_inference():
    draft = {'proposal': {'analyst_review': {'earnings': {'source_ids': ['news:1']}}},
             'previous': {'citations': [{'source_id': 'news:old-context'}]}}
    with patch.object(reassess, 'call_llm', return_value=(None, 'offline_stop')) as model:
        with pytest.raises(ValueError, match='Candidate source not in review bundle: news:1'):
            claim_evidence.semantic_review(draft, data(), {}, '', '')
        model.assert_not_called()


def test_all_candidate_citation_forms_fail_closed_before_review():
    for reference in ({'evidence_ids': ['news:1']}, {'source_ids': ['news:1']}, {'source_id': 'news:1'}):
        draft = {'proposal': {'monitoring': reference},
                 'previous': {'source_id': 'news:historical'}}
        with patch.object(reassess, 'call_llm', return_value=({'verdict': 'supported',
                'citations': [{'source_id': 'S1'}], 'issues': [], 'counterargument': 'Uncertain future.'}, 'ok')) as model:
            with pytest.raises(ValueError, match='Candidate source not in review bundle: news:1'):
                claim_evidence.semantic_review(draft, data(), {}, '', '')
            model.assert_not_called()


def test_real_outer_prompts_and_validation_share_canonical_bundle(monkeypatch, tmp_path):
    import copy
    from datetime import datetime, timezone
    import decision_lifecycle
    import weekly_round
    from tests.test_decision_lifecycle import thesis
    from tests.test_reassess import PORTFOLIO
    rows = data()
    expected = llm_context.research_view(rows)['MU']['source_documents']
    moment = datetime(2026, 10, 3, 15, tzinfo=timezone.utc)
    class Checked(Exception):
        pass
    def check_validation(monitoring, symbol, position, supplied, *args):
        assert supplied['MU']['source_documents'] == expected
        raise Checked
    monkeypatch.setattr(decision_lifecycle, 'validate_monitoring', check_validation)
    for path in ('claim', 'thesis', 'weekly'):
        calls = []
        def transport(messages, **kwargs):
            user = messages[1]['content']
            calls.append(user)
            if path == 'claim' and len(calls) == 2:  # actual claim semantic-review transport
                sources = json.loads(user)['sources']
                assert {s['title']: s['text'] for s in sources.values()} == {
                    s['title']: s['text'] for s in expected.values()}
                raise Checked
            if path == 'weekly':
                supplied = json.JSONDecoder().raw_decode(user)[0]['weekly_data.json']['MU']['source_documents']
            else:
                supplied = json.JSONDecoder().raw_decode(user.split('NEWS SOURCE EVIDENCE:\n', 1)[1])[0]['documents']
            assert supplied == expected
            assert 'news:1' not in supplied
            if path == 'claim':
                return json.dumps({'text': 'Demand remains uncertain.', 'status': 'valid'})
            if path == 'thesis':
                allowed = json.JSONDecoder().raw_decode(user.split('ALLOWED MONITORING evidence_ids (issuer only; benchmarks cannot justify threshold changes):\n')[1])[0]
                assert set(allowed) == set(expected)
                return json.dumps({'thesis_assessment': 'Demand remains uncertain.', 'monitoring': {},
                                   'decision': {'action': 'HOLD', 'reasoning': 'Await evidence.',
                                                'falsifier': 'Demand weakens.'}})
            return json.dumps({'decisions': [{'symbol': 'MU', 'monitoring': {}}]})
        monkeypatch.setattr(reassess.llm_transport, 'complete', transport)
        report = {'data': copy.deepcopy(rows), 'triggered': [{'symbol': 'MU', 'claim_id': 'MU-1',
                  'severity': path, 'trigger': 'Review evidence'}]}
        with pytest.raises(Checked):
            if path == 'claim':
                reassess.claim_flow({'MU': thesis()}, report, copy.deepcopy(PORTFOLIO), moment,
                                   'fake', 'fake', {'calls': 0}, 60, False, False)
            elif path == 'thesis':
                reassess.thesis_flow({'MU': thesis()}, report, copy.deepcopy(PORTFOLIO), moment,
                                    'fake', 'fake', {'calls': 0}, False,
                                    str(tmp_path/'notes'), str(tmp_path/'decisions'))
            else:
                class Clock:
                    @staticmethod
                    def now(tz): return moment
                monkeypatch.setattr(weekly_round, 'datetime', Clock)
                monkeypatch.setattr(weekly_round, 'already_done', lambda *args: False)
                monkeypatch.setattr(weekly_round.llm_transport, 'credential', lambda: 'fake')
                real_read = weekly_round.read_json
                weekly_rows = dict(rows, _meta={'date': moment.date().isoformat()})
                monkeypatch.setattr(weekly_round, 'read_json', lambda path, default: weekly_rows
                    if path.endswith('weekly_data.json') else real_read(path, default))
                monkeypatch.setattr(weekly_round, 'write_json', lambda *args: None)
                monkeypatch.setattr('sys.argv', ['weekly_round', '--dry-run'])
                weekly_round.main()
        assert rows == data()
