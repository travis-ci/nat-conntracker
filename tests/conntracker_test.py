from netaddr import IPAddress

from nat_conntracker.conntracker import Conntracker


def test_conntracker_init():
    ctr = Conntracker(None, None)
    assert ctr.src_ign is not None
    assert ctr.dst_ign is not None
    assert ctr.stats is not None


def test_private_nets():
    assert len(Conntracker.PRIVATE_NETS) > 0
    covers_local = False
    for net in Conntracker.PRIVATE_NETS:
        if IPAddress('10.10.0.99') in net:
            covers_local = True
    assert covers_local
