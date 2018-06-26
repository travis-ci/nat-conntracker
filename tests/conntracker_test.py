import logging

import pytest

from nat_conntracker.conntracker import Conntracker
from nat_conntracker.flow_parser import Flow


@pytest.fixture
def empty_conntracker():
    return Conntracker(None, None, None, None, None)


def test_conntracker_init(empty_conntracker):
    assert empty_conntracker._settings is None
    assert empty_conntracker._syncer is None
    assert empty_conntracker._logger is None
    assert empty_conntracker._stats is None


def test_conntracker_handle_flow(empty_conntracker):
    empty_conntracker._logger = logging.getLogger()

    assert empty_conntracker.handle_flow(None) is None

    empty_flow = Flow()
    empty_flow.flowtype = 'new'
    assert empty_conntracker.handle_flow(empty_flow) is None
