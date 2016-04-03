"""A utility for dealing with tmux layout information."""
import re


class Layout(object):
    def __init__(self, x, y, size, identifier=-1, vertical=False):
        self._depth = -1
        self.parent = None
        self.x = x
        self.y = y
        self.size = tuple(size)
        self.x2 = x + self.size[0]
        self.y2 = y + self.size[1]
        self.identifier = identifier
        self.vertical = vertical
        self.panes = []

    def copy(self):
        l = Layout(self.x, self.y, self.size, self.identifier,
                   vertical=self.vertical)
        l.parent = self.parent
        return l

    @property
    def depth(self):
        if self._depth == -1:
            self._depth = 0
            p = self
            while p.parent is not None:
                p = p.parent
                self._depth += 1
        return self._depth

    @property
    def coords(self):
        return (self.x, self.y)

    @property
    def dimensions(self):
        return (self.x, self.y, self.x2, self.y2)

    def is_intersect(self, other):
        return self.x < other.x2 and self.x2 > other.x \
            and self.y < other.y2 and self.y2 > other.y

    def is_inside(self, other):
        return self.x >= other.x and self.y >= other.y \
            and self.x2 <= other.x2 and self.y2 <= other.y2

    def __hash__(self):
        return hash(('layout', self.identifier, self.x, self.y) + self.size)

    def __eq__(self, other):
        return isinstance(other, Layout) \
            and hash(other.identifier) == hash(self.identifier)

    def _describe(self, depth=0):
        out = '  ' * depth
        pv = '-' if not self.parent else self.parent.vertical
        out += '{}Layout(id:{} x:{} y:{} x2:{}, y2:{}) (pv: {})\n' \
            .format('Vertical' if self.vertical else 'Horizontal',
                    self.identifier, self.x, self.y, self.x2, self.y2, pv)
        for p in self.panes:
            out += p._describe(depth + 1)
        return out

    def __repr__(self):
        return self._describe()


def layout_end(layout):
    """Find the ending token for the layout."""
    tok = layout[0]
    if tok == '{':
        end = '}'
    elif tok == '[':
        end = ']'
    else:
        return -1

    skip = -1
    for i, c in enumerate(layout):
        if c == end and skip == 0:
            return i
        elif c == end and skip > 0:
            skip -= 1
        elif c == tok:
            skip += 1
    return -1


def layout_split(layout):
    """Break the layout into segments that are easier to parse.

    The layout is: size, x, y, identifier.  The identifier is not a number when
    the pane is split.  A square bracket is a vertical split, and a curly
    bracket is a horizontal split.
    """
    parts = []
    last_i = 0
    i = 0
    l = len(layout)

    while i < l:
        c = layout[i]
        if c in (',', '{', '['):
            m = re.match(r'((?:\d+x)?\d+)', layout[last_i:])
            if m:
                parts.append(m.group(1))
                last_i = i + 1
                c = layout[i]
            else:
                last_i = i + 1
        if c in ('{', '['):
            end = layout_end(layout[i:])
            parts.append(layout[i:i+end+1])
            i += end + 1
            last_i = i
            continue
        i += 1

    if last_i < l:
        trailing = layout[last_i:]
        m = re.match(r'(\d+)', trailing)
        if m:
            parts.append(m.group(1))
    return parts


def make_layout(size, x, y, identifier, parent=None):
    """Create a layout object.

    Extract more layouts if the identifier is not a number.
    """
    size = map(int, size.split('x', 1))
    x = int(x)
    y = int(y)

    layout = Layout(x, y, size)
    layout.parent = parent
    if identifier.startswith(('{', '[')):
        layout.vertical = identifier[0] == '['
        layout.panes = extract_layout(identifier[1:-1], layout)
    else:
        if parent:
            layout.vertical = parent.vertical
        layout.identifier = int(identifier)
    return layout


def extract_layout(layout, parent=None):
    """Extract layout information from a layout string."""
    layout = layout_split(layout)
    panes = []
    for i in range(0, len(layout), 4):
        args = layout[i:i+4][:] + [parent]
        panes.append(make_layout(*args))
    return panes


def parse_layout(layout):
    """Parse the main layout string.

    The first segment is a unique window ID or something.
    """
    # Main x,y should be 0
    _, layout = layout.split(',', 1)
    root = extract_layout(layout)[0]
    return root
