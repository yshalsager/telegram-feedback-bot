"""Unit tests for broadcast filter parsing helpers."""

from datetime import UTC, datetime, timedelta

import pytest
from feedback_bot.telegram.utils.broadcast import parse_broadcast_filters


@pytest.mark.parametrize(
    ('raw', 'expected_keys'),
    [
        ('', []),
        ('done', []),
        ('joined_after 2024-01-01', ['joined_after']),
        (
            'joined_before 2024-02-01\nusername_only yes',
            ['joined_before', 'username_only'],
        ),
    ],
)
def test_parse_broadcast_filters_returns_expected_keys(raw, expected_keys):
    filters, error = parse_broadcast_filters(raw)

    assert error is None
    assert list(filters.keys()) == expected_keys
    for key in expected_keys:
        if key.endswith(('after', 'before')):
            assert filters[key].tzinfo is UTC


def test_parse_broadcast_filters_active_within():
    filters, error = parse_broadcast_filters('active_within 3')

    assert error is None
    assert 'active_after' in filters
    expected = datetime.now(UTC) - timedelta(days=3)
    assert abs(filters['active_after'] - expected) < timedelta(seconds=5)


@pytest.mark.parametrize(
    ('raw', 'message'),
    [
        ('joined_after not-a-date', 'Invalid date for "joined_after". Use YYYY-MM-DD.'),
        ('sample_every zero', 'Invalid number for "sample_every".'),
        ('sample_every 0', '"sample_every" must be at least 1.'),
        ('username_only nope', None),
        ('unknown option', 'Unrecognized filter: "unknown option".'),
    ],
)
def test_parse_broadcast_filters_errors(raw, message):
    filters, error = parse_broadcast_filters(raw)

    if message is None:
        assert error is None
        assert filters['username_only'] is False
    else:
        assert filters == {}
        assert error == message
