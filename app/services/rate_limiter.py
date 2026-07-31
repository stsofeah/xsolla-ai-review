import time

WINDOW_SECONDS = 60
MAX_REQUESTS = 30

_requests: list[float] = []


def allow_request() -> tuple[bool, int]:
    now = time.time()

    while _requests and _requests[0] <= now - WINDOW_SECONDS:
        _requests.pop(0)

    if len(_requests) >= MAX_REQUESTS:
        retry_after = int(WINDOW_SECONDS - (now - _requests[0])) + 1
        return False, retry_after

    _requests.append(now)
    return True, 0