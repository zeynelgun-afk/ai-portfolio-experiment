import analyst_health


def test_quarantined_observations_are_reported_without_discarding_healthy_coverage():
    data = {'_meta': {},
            'MU': {'analyst_revisions': {'status': 'ok', 'estimates_status': 'ok'}},
            'AMD': {'analyst_revisions': {'status': 'incomplete', 'estimates_status': 'ok'}},
            'NVDA': {'analyst_revisions': {'status': 'unavailable', 'estimates_status': 'ok'}},
            'TLN': {'analyst_revisions': {'status': 'ok', 'estimates_status': 'unavailable'}}}
    assert analyst_health.classify(data) == (['NVDA', 'TLN'], ['AMD'])
