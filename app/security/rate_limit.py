from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int = 0


class SlidingWindowRateLimiter:
    """
    Simple in-memory per-key sliding-window rate limiter.

    Suitable for this local security lab.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        self.requests = defaultdict(
            deque
        )

    def check(
        self,
        key: str
    ) -> RateLimitResult:

        now = monotonic()

        request_times = self.requests[
            key
        ]

        # Remove entries outside the window.
        while (
            request_times
            and now - request_times[0]
            >= self.window_seconds
        ):
            request_times.popleft()

        if (
            len(request_times)
            >= self.max_requests
        ):
            oldest = request_times[0]

            retry_after = int(
                self.window_seconds
                - (now - oldest)
            ) + 1

            return RateLimitResult(
                allowed=False,
                remaining=0,
                retry_after_seconds=retry_after,
            )

        request_times.append(
            now
        )

        remaining = (
            self.max_requests
            - len(request_times)
        )

        return RateLimitResult(
            allowed=True,
            remaining=remaining,
        )

agent_rate_limiter = SlidingWindowRateLimiter(
    max_requests=10,
    window_seconds=60
)

transfer_rate_limiter = SlidingWindowRateLimiter(
    max_requests=3,
    window_seconds=300
)