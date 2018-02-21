from netaddr import IPAddress

from nat_conntracker.conntracker import Conntracker, PRIVATE_NETS


def test_conntracker_init():
    ctr = Conntracker(None)
    assert ctr.ignore is not None
    assert ctr.stats is not None


def test_private_nets():
    assert len(PRIVATE_NETS) > 0
    covers_local = False
    for net in PRIVATE_NETS:
        if IPAddress('10.10.0.99') in net:
            covers_local = True
    assert covers_local
