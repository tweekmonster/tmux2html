from __future__ import print_function

import sys
import subprocess

from . import tmux_layout


def shell_cmd(cmd):
    """Execute a command.

    Exits if the command fails.
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print(stderr.decode('utf8'), file=sys.stderr)
        sys.exit(1)
    return stdout.decode('utf8')


def get_contents(target):
    """Get the contents of a target pane.

    The content is unwrapped lines and may be longer than the pane width.
    """
    content = shell_cmd([
        'tmux',
        'capture-pane',
        '-epJS', '-0',
        '-t', str(target),
    ])

    lines = content.split('\n')
    return '\n'.join(lines)


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


def update_pane_list(pane, window=None, session=None):
    root = get_layout(window, session)
    panes2 = pane_list(root, list_all=True)
    for p in panes2:
        if p.identifier == pane.identifier:
            return p, pane_list(p)


def get_layout(window=None, session=None):
    """Get the tmux layout string.

    Defaults to the current session and/or current window.
    """
    cmd = ['tmux', 'list-windows']
    if session is not None:
        cmd.extend(['-t', str(session)])
    lines = shell_cmd(cmd)
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
