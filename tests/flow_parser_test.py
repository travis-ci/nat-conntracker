from nat_conntracker.flow_parser import FlowParser


def test_flow_parser_init():
    flp = FlowParser(None, None)
    assert flp is not None
