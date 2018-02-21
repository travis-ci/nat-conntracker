from nat_conntracker.stats import Stats


def test_stats_init():
    stats = Stats()
    assert stats.max_size > 0
    assert stats.counter is not None
    assert stats.index is not None
