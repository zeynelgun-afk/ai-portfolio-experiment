import copy
import json
from datetime import timedelta
from pathlib import Path
import pytest
import analyst_revisions as ar

ROWS = json.loads(Path(__file__).with_name('target_quarantine_records.json').read_text())

@pytest.mark.parametrize('symbol', ROWS)
def test_actual_attribution_quarantine_breaks_both_firm_segments(symbol):
    raw = ROWS[symbol]
    at = ar.stamp(raw['publishedDate'])
    title_firm = {'AMD': 'BofA Securities', 'ANET': 'Evercore ISI', 'NVDA': 'JPMorgan'}[symbol]
    before = []
    after = []
    for firm in (raw['analystCompany'], title_firm):
        for age, target, dest in ((-2, 100, before), (-1, 110, before), (1, 120, after)):
            dest.append(dict(raw, analystCompany=firm, newsTitle='Target review',
                priceTarget=target, adjPriceTarget=target,
                publishedDate=(at+timedelta(days=age)).isoformat()))
    frozen = copy.deepcopy(raw)
    for rows in (before+[raw], before+[raw]+after):
        result = ar.analyze(symbol, rows, at+timedelta(days=2), True)
        assert result['status'] == 'incomplete'
        assert result['quarantined_records'][0]['raw_record'] == frozen
        assert result['windows']['30']['matched_firms'] == 0
        assert result['windows']['30']['unpaired_firms'] == (2 if after[-1] in rows else 0)
        assert ar.review_trigger(symbol, result, {}, at+timedelta(days=2)) is None
    assert raw == frozen


def test_numeric_quarantine_blocks_same_day_and_requires_two_later_clean_records():
    from tests.test_analyst_revisions import NOW, row
    bad = row('Alpha', 115, 2)
    bad['newsTitle'] = 'MU PT Raised to $999 at Alpha'
    baseline = [row('Alpha', 100, 5), row('Alpha', 110, 3), bad, row('Alpha', 116, 2)]
    report = ar.analyze('MU', baseline+[row('Alpha', 120, 1)], NOW, True)
    assert report['windows']['30']['matched_firms'] == 0
    assert report['windows']['30']['unpaired_firms'] == 1
    report = ar.analyze('MU', baseline+[row('Alpha', 120, 1), row('Alpha', 130, 0)], NOW, True)
    assert report['windows']['30']['matched_firms'] == 1
    assert report['windows']['30']['revisions'][0]['previous']['target_raw'] == 120
    assert report['quarantined_records'][0]['raw_record'] == bad
    assert report['status'] == 'incomplete'
