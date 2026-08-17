import app.security.rate_limit as rate_module

from app.security.rate_limit import (
    SlidingWindowRateLimiter,
)


def test_requests_are_allowed_up_to_limit(
    monkeypatch,
):
    now = [100.0]

    monkeypatch.setattr(
        rate_module,
        "monotonic",
        lambda: now[0],
    )

    limiter = SlidingWindowRateLimiter(
        max_requests=3,
        window_seconds=60,
    )

    first = limiter.check("alice")
    second = limiter.check("alice")
    third = limiter.check("alice")

    assert first.allowed is True
    assert first.remaining == 2

    assert second.allowed is True
    assert second.remaining == 1

    assert third.allowed is True
    assert third.remaining == 0


def test_request_over_limit_is_denied(
    monkeypatch,
):
    now = [100.0]

    monkeypatch.setattr(
        rate_module,
        "monotonic",
        lambda: now[0],
    )

    limiter = SlidingWindowRateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    limiter.check("alice")
    limiter.check("alice")

    result = limiter.check("alice")

    assert result.allowed is False
    assert result.remaining == 0

    assert (
        result.retry_after_seconds
        > 0
    )


def test_rate_limit_is_isolated_per_user(
    monkeypatch,
):
    now = [100.0]

    monkeypatch.setattr(
        rate_module,
        "monotonic",
        lambda: now[0],
    )

    limiter = SlidingWindowRateLimiter(
        max_requests=1,
        window_seconds=60,
    )

    alice_first = limiter.check(
        "alice"
    )

    alice_second = limiter.check(
        "alice"
    )

    bob_first = limiter.check(
        "bob"
    )

    assert alice_first.allowed is True
    assert alice_second.allowed is False

    # Alice exhausting her quota
    # must not exhaust Bob's quota.
    assert bob_first.allowed is True


def test_requests_are_allowed_after_window_expires(
    monkeypatch,
):
    now = [100.0]

    monkeypatch.setattr(
        rate_module,
        "monotonic",
        lambda: now[0],
    )

    limiter = SlidingWindowRateLimiter(
        max_requests=1,
        window_seconds=60,
    )

    first = limiter.check("alice")

    assert first.allowed is True

    blocked = limiter.check("alice")

    assert blocked.allowed is False

    # Move beyond the sliding window.
    now[0] = 161.0

    allowed_again = limiter.check(
        "alice"
    )

    assert allowed_again.allowed is True