import sys
import subprocess


def shell_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print(stderr.decode('utf8'), file=sys.stderr)
        sys.exit(1)
    return stdout.decode('utf8')


def get_panesize(target):
    size = shell_cmd([
        'tmux',
        'display',
        '-p',
        '-t', target,
        '#{pane_width}x#{pane_height}',
    ])
    return tuple(map(int, size.split('x', 1)))


def get_contents(target):
    size = get_panesize(target)
    content = shell_cmd([
        'tmux',
        'capture-pane',
        '-epJS', '-0',
        '-t', target,
    ])

    lines = content.split('\n')[:size[1]]
    return '\n'.join(lines)
