from collections import namedtuple
from xml.dom.minidom import parseString as minidom_parse_string
from xml.parsers.expat import ExpatError

__all__ = ['FlowParser']


class FlowParser(object):
    def __init__(self, conntracker, logger):
        self._conntracker = conntracker
        self._logger = logger

    def handle_events(self, stream, is_done=None):
        is_done = is_done if is_done is not None else lambda: False
        for line in stream:
            try:
                dom = minidom_parse_string(line)
                for flow_node in dom.getElementsByTagName('flow'):
                    self._conntracker.handle_flow(Flow.from_node(flow_node))
            except ExpatError as experr:
                self._logger.debug(f'expat error: {experr}')
            finally:
                self._logger.debug(f'checking is_done={is_done()}')
                if is_done():
                    return


FlowAddress = namedtuple('FlowAddress', ['host', 'port'])


class FlowMetaGeneric(object):
    def __init__(self):
        self.direction = ''

    def __repr__(self):
        return f'<{self.__class__.__name__} direction={repr(self.direction)}>'

    @classmethod
    def from_node(cls, meta_node):
        inst = cls()
        inst.direction = meta_node.getAttribute('direction')
        return inst


class FlowMetaOrigReply(object):
    def __init__(self):
        self.direction = ''
        self.src = None
        self.dst = None

    def __repr__(self):
        return f'<{self.__class__.__name__} direction={repr(self.direction)} ' \
                f'src={repr(self.src)} dst={repr(self.dst)}>'

    @classmethod
    def from_node(cls, meta_node):
        inst = cls()
        inst.direction = meta_node.getAttribute('direction')
        inst.src = FlowAddress(
            _find_data(meta_node, 'src'), _find_data(meta_node, 'sport'))
        inst.dst = FlowAddress(
            _find_data(meta_node, 'dst'), _find_data(meta_node, 'dport'))
        return inst


class FlowMetaIndependent(object):
    direction = 'independent'

    def __init__(self):
        self.id = ''
        self.assured = False

    def __repr__(self):
        return f'<{self.__class__.__name__} id={repr(self.id)} ' \
                f'assured={repr(self.assured)}>'

    @classmethod
    def from_node(cls, meta_node):
        inst = cls()
        inst.id = _find_data(meta_node, 'id')
        if len(meta_node.getElementsByTagName('assured')) > 0:
            inst.assured = True
        return inst


class Flow(object):
    def __init__(self):
        self.flowtype = ''
        self.meta = []

    def __repr__(self):
        return f'<{self.__class__.__name__} flowtype={repr(self.flowtype)} ' \
                f'meta={repr(self.meta)}>'

    def src_dst(self):
        for meta in self.meta:
            if meta.direction != 'original':
                continue
            if meta.src is not None and meta.dst is not None:
                return (meta.src, meta.dst)
        return (None, None)

    @classmethod
    def from_node(cls, flow_node):
        inst = cls()
        inst.flowtype = flow_node.getAttribute('type')
        for meta_node in flow_node.getElementsByTagName('meta'):
            inst.meta.append(cls.meta_from_node(meta_node))
        return inst

    @staticmethod
    def meta_from_node(meta_node):
        return {
            'original': FlowMetaOrigReply,
            'reply': FlowMetaOrigReply,
            'independent': FlowMetaIndependent
        }.get(meta_node.getAttribute('direction'),
              FlowMetaGeneric).from_node(meta_node)


def _find_data(node, parent_tag, default=''):
    for subnode in node.getElementsByTagName(parent_tag):
        if subnode.firstChild is not None:
            return subnode.firstChild.data
    return default
