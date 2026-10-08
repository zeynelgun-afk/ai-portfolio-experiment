"""Known missing coverage is not complete just because it was reported today."""
from datetime import datetime, timezone
import detector


def test_cached_incomplete_analyst_coverage_remains_partial_and_is_persisted():
    report = detector.run({'AMD': {'claims': [], 'monitoring': {}}},
        {'AMD': {'analyst_refreshed': False, 'analyst_revisions': {
            'status': 'incomplete', 'estimates_status': 'ok',
            'coverage': {'pagination_complete': True},
            'quarantined_records': [{'reason': 'conflicting source attribution'}]}}},
        {}, {}, {}, datetime(2026, 10, 8, 19, tzinfo=timezone.utc), assess_news=False)
    assert len(report['news_errors']) == 1
    assert 'coverage incomplete' in report['news_errors'][0]['error']
    assert report['state_changed'] is True
