"""Exact non-numeric labels from the failed detector log must not be numbers."""
import pytest
import evidence


def test_recorded_publisher_alias_is_not_a_measured_number():
    for name in ('247 Wall St', '247 Wallst', '24/7 Wall Street'):
        prose = name + ' describes an AI investment-versus-return gap'
        assert evidence.render(prose, {}) == prose
        with pytest.raises(ValueError, match='Raw numeric'):
            evidence.render(prose + ' of 99 percent', {})


def test_twenty_day_average_requires_supplied_volume_metric_and_reference():
    facts = evidence.ledger({'MU': {'volume_avg_20d': 42, 'price_date': '2026-10-02'}},
                            '2026-10-03', 'fixture')
    prose = 'Volume is below the 20-day average of {{MU.volume_avg_20d}}.'
    assert 'volume_avg_20d: 42 shares' in evidence.render(prose, facts)
    for invalid, ledger in [(prose, {}), ('20-day average is 99 shares', facts),
                            ('90-day average of {{MU.volume_avg_20d}}', facts)]:
        with pytest.raises(ValueError, match='Raw numeric'):
            evidence.render(invalid, ledger)
