import threading
import time

import pytest

from tradingagents.dataflows.stockstats_utils import YF_MAX_CONCURRENCY, yf_retry


@pytest.mark.unit
def test_yf_retry_caps_concurrent_calls():
    current = 0
    max_seen = 0
    lock = threading.Lock()

    def work():
        nonlocal current, max_seen
        with lock:
            current += 1
            max_seen = max(max_seen, current)
        time.sleep(0.05)
        with lock:
            current -= 1
        return "ok"

    threads = [
        threading.Thread(target=lambda: yf_retry(work))
        for _ in range(YF_MAX_CONCURRENCY + 4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert max_seen <= YF_MAX_CONCURRENCY
    assert max_seen >= 2  # proves calls genuinely overlapped up to the cap
