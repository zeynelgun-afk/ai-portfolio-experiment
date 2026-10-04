"""Tests must never consume live subscription inference accidentally."""
import pytest


@pytest.fixture(autouse=True)
def no_live_hermes(monkeypatch, request):
    if request.node.path.name == 'test_local_hermes.py':
        return  # these tests mock the CLI process boundary
    import llm_transport
    def forbidden(*args, **kwargs):
        raise AssertionError('Mock llm_transport.complete: live inference is forbidden in tests')
    monkeypatch.setattr(llm_transport, 'complete', forbidden)
