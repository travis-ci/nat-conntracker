from nat_conntracker import Conntracker


def test_conntracker_init():
    ctr = Conntracker()
    assert ctr.ignore is not None
    assert ctr.stats is not None
