# coding: utf8
from __future__ import print_function

import io
import sys
import gzip
import subprocess
import unicodedata
from base64 import b64encode

from . import tmux_layout


def compress_data(s, line_len=200):
    b = io.BytesIO()
    with gzip.GzipFile(fileobj=b, mode='w') as fp:
        fp.write(s.encode('utf8'))
    hunks = []
    data = b64encode(b.getvalue()).decode('utf8')
    for i in range(0, len(data), line_len):
        hunks.append(data[i:i+line_len])
    return hunks


def shell_cmd(cmd, ignore_error=False):
    """Execute a command.

    Exits if the command fails.
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if not ignore_error and p.returncode != 0:
        print(stderr.decode('utf8'), file=sys.stderr)
        sys.exit(1)
    try:
        ret = stdout.decode('utf8')
    except UnicodeDecodeError as e:
        print(e, file=sys.stderr)
        ret = "…"
    return ret


def get_contents(target, full=False, max_lines=0):
    """Get the contents of a target pane.

    The content is unwrapped lines and may be longer than the pane width.
    """
    if full:
        if max_lines:
            args = ['-S', str(-max_lines), '-E', '-']
        else:
            args = ['-S', '-', '-E', '-']
    else:
        args = ['-S', '-0']
        pos = shell_cmd([
            'tmux',
            'display-message',
            '-p', '-t', str(target),
            '-F', '#{scroll_position}/#{scroll_region_lower}'
        ], ignore_error=True)

        if pos:
            pos, height = pos.split('/')
            if pos:
                pos = int(pos) * -1
                height = int(height)
                args = ['-S', str(pos), '-E', str(pos + height)]

    content = shell_cmd([
        'tmux',
        'capture-pane',
        '-epJ',
        '-t', str(target),
    ] + args, ignore_error=True)

    lines = content.split('\n')
    return '\n'.join(lines)


def get_cursor(target):
    cmd = ['tmux', 'display-message', '-p', '-t', str(target),
           '#{pane_active},#{cursor_x},#{cursor_y}']
    output = shell_cmd(cmd, ignore_error=True)
    try:
        output = [int(x) for x in output.split(',')]
    except ValueError:
        print(cmd, output)
        return (-1, -1)
    if output[0]:
        return [x for x in output[1:]]
    return (-1, -1)


def str_width(s):
    """Return the width of the string.

    Takes the width of East Asian characters into account
    """
    return sum([2 if unicodedata.east_asian_width(c) == 'W' else 1 for c in s])


def pane_list(pane, ids=None, list_all=False):
    """Get a list of panes.

    This makes it easier to target panes from the command line.
    """
    if ids is None:
        ids = []
    if list_all or pane.identifier != -1:
        ids.append(pane)
    for p in pane.panes:
        pane_list(p, ids, list_all=list_all)

    return ids


def update_pane_list(pane, window=None, session=None, ignore_error=True):
    """Updates the pane list.

    This searches for a pane that matches the dimensions of the supplied (old)
    pane.  When a pane is not split, it will not have panes and the size will
    take up its entire block.  When it's split, the pane is moved into pane
    that wraps it and the new split.  The new pane will now take the dimensions
    of the old pane.  Naïvely matching the pane identifier would result in a
    shrinking pane when capturing an animation.
    """
    root = get_layout(window, session, ignore_error=ignore_error)
    panes = pane_list(root, list_all=True)
    n_pane = pane.copy()
    n_pane.identifier = -1
    # n_pane.vertical = False
    collected = []
    panes2 = []
    x = 99999
    y = 99999
    x2 = 0
    y2 = 0
    for p in panes:
        if p.is_inside(n_pane) and p.dimensions not in collected:
            for p2 in pane_list(p, list_all=True):
                collected.append(p2.dimensions)
            panes2.append(p)
            x = min(x, p.x)
            y = min(y, p.y)
            x2 = max(x2, p.x2)
            y2 = max(y2, p.y2)

    n_pane.panes = panes2
    n_pane.x = x
    n_pane.y = y
    n_pane.x2 = x2
    n_pane.y2 = y2
    n_pane.size = (n_pane.x2 - n_pane.x, n_pane.y2 - n_pane.y)
    return n_pane, pane_list(n_pane), tuple(collected)


def get_layout(window=None, session=None, ignore_error=False):
    """Get the tmux layout string.

    Defaults to the current session and/or current window.
    """
    cmd = ['tmux', 'list-windows', '-F',
           '#F,#{window_layout}']
    if session is not None:
        cmd.extend(['-t', str(session)])
    lines = shell_cmd(cmd, ignore_error=ignore_error)
    windows = []
    active = None
    for line in lines.strip().split('\n'):
        flag, layout = line.split(',', 1)
        root = tmux_layout.parse_layout(layout)
        if flag == '*':
            root.active = True
            active = root
        windows.append(root)

    if window is None:
        return active

    return windows[window]
