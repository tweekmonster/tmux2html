# coding: utf8
from __future__ import print_function

import sys
import subprocess
import unicodedata

from . import tmux_layout


def shell_cmd(cmd, ignore_error=False):
    """Execute a command.

    Exits if the command fails.
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if not ignore_error and p.returncode != 0:
        print(stderr.decode('utf8'), file=sys.stderr)
        sys.exit(1)
    return stdout.decode('utf8')


def get_contents(target, full=False):
    """Get the contents of a target pane.

    The content is unwrapped lines and may be longer than the pane width.
    """
    content = shell_cmd([
        'tmux',
        'capture-pane',
        '-epJS', '-' if full else '-0',
        '-t', str(target),
    ])

    lines = content.split('\n')
    return '\n'.join(lines)


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
    panes2 = pane_list(root, list_all=True)

    for p in panes2:
        if p.dimensions == pane.dimensions:
            return p, pane_list(p)
    return pane, pane_list(pane)


def get_layout(window=None, session=None, ignore_error=False):
    """Get the tmux layout string.

    Defaults to the current session and/or current window.
    """
    cmd = ['tmux', 'list-windows']
    if session is not None:
        cmd.extend(['-t', str(session)])
    lines = shell_cmd(cmd, ignore_error=ignore_error)
    windows = []
    active = None
    for line in lines.strip().split('\n'):
        i = line.find('[layout')
        root = tmux_layout.parse_layout(line[i:].split()[1])
        if line.endswith('(active)'):
            root.active = True
            active = root
        windows.append(root)

    if window is None:
        return active

    return windows[window]
