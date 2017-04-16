# coding: utf8
from __future__ import print_function, unicode_literals, division

import os
import re
import sys
import json
import time
import argparse
import tempfile
import unicodedata
from collections import defaultdict

from . import color, utils, tpl

try:
    from html import escape
except ImportError:
    from cgi import escape

try:
    str_ = unicode
    chr_ = unichr
    py_v = 2
except NameError:
    str_ = str
    chr_ = chr
    py_v = 3


class IncompatibleOptionError(Exception):
    pass


basedir = os.path.dirname(__file__)
classname = 'tmux-html'


font_stack = (
    'Anonymice Powerline',
    'Arimo for Powerline',
    'Aurulent Sans Mono',
    'Bitstream Vera Sans Mono',
    'Cousine for Powerline',
    'DejaVu Sans Mono for Powerline',
    'Droid Sans Mono Dotted for Powerline',
    'Droid Sans Mono Slashed for Powerline',
    'Droid Sans Mono for Powerline',
    'Fira Mono Medium for Powerline',
    'Fira Mono for Powerline',
    'Fura Mono Medium for Powerline',
    'Fura Mono for Powerline',
    'Hack',
    'Heavy Data',
    'Hurmit',
    'IBM 3270',
    'IBM 3270 Narrow',
    'Inconsolata for Powerline',
    'Inconsolata-dz for Powerline',
    'Inconsolata-g for Powerline',
    'Knack',
    'Lekton',
    'Literation Mono Powerline',
    'M+ 1m',
    'Meslo LG L DZ for Powerline',
    'Meslo LG L for Powerline',
    'Meslo LG M DZ for Powerline',
    'Meslo LG M for Powerline',
    'Meslo LG S DZ for Powerline',
    'Meslo LG S for Powerline',
    'ProFontWindows',
    'ProggyCleanTT',
    'ProggyCleanTT CE',
    'Roboto Mono Light for Powerline',
    'Roboto Mono Medium for Powerline',
    'Roboto Mono Thin for Powerline',
    'Roboto Mono for Powerline',
    'Sauce Code Powerline',
    'Sauce Code Pro',
    'Sauce Code Pro Black',
    'Sauce Code Pro ExtraLight',
    'Sauce Code Pro Light',
    'Sauce Code Pro Medium',
    'Sauce Code Pro Semibold',
    'Source Code Pro Black for Powerline',
    'Source Code Pro ExtraLight for Powerline',
    'Source Code Pro Light for Powerline',
    'Source Code Pro Medium for Powerline',
    'Source Code Pro Semibold for Powerline',
    'Symbol Neu for Powerline',
    'Tinos for Powerline',
    'Ubuntu Mono for Powerline',
    'Ubuntu Mono derivative Powerlin',
    'Ubuntu Mono derivative Powerline',
    'monofur for Powerline',
)

# The following table is referenced from:
# https://en.wikipedia.org/wiki/Talk%3AVT100#Alternate_character_set
vt100_alt_charset = {
    'enabled': False,
    'table': [
        #    0       1       2       3       4       5       6       7
        0x25c6, 0x2592, 0x2409, 0x240c, 0x240d, 0x240a, 0x00b0, 0x00b1,
        #    8       9       A       B       C       D       E       F
        0x2424, 0x240b, 0x2518, 0x2510, 0x250c, 0x2514, 0x253c, 0x23ba,
        #    0       1       2       3       4       5       6       7
        0x23bb, 0x2500, 0x23bc, 0x23bd, 0x251c, 0x2524, 0x2534, 0x252c,
        #    8       9       A       B       C       D       E       F
        0x2502, 0x2264, 0x2265, 0x03c0, 0x2260, 0x00a3, 0x00b7, 0x0020
    ],
}


class Pane(object):
    def __init__(self, size, max_lines=0):
        self.size = size
        self.max_lines = max_lines
        self.lines = []

    def add_line(self, line):
        self.lines.append(line)

    def __len__(self):
        return len(self.lines)

    def __str__(self):
        html_lines = [str_(x) for x in self.lines]
        if self.max_lines and len(self.lines) > self.size[1]:
            visible = html_lines[-self.size[1]:]
            hidden = html_lines
        else:
            visible = html_lines
            hidden = []

        out = '<pre>{}</pre>'.format(''.join(visible))
        if hidden:
            out += '<script type="text/tmux-data">{}</script>' \
                .format(''.join(utils.compress_data('\n'.join(hidden))))
        return out


class ChunkedLine(object):
    def __init__(self, renderer, width=0, line=0):
        self.col = renderer.column
        self.line = line
        self.renderer = renderer
        self.width = width
        self.length = 0
        self.chunks = []
        self.tag_stack = []
        self._curtag_args = []

    def _style_classes(self, styles):
        """Set an equivalent CSS style."""
        out = []
        if 1 in styles and 22 not in styles:
            # Bold
            out.append('sb')
        if 3 in styles and 23 not in styles:
            # Italic
            out.append('si')
        if 4 in styles and 24 not in styles:
            # Underline
            out.append('su')
        return out

    def _escape_text(self, s):
        """Escape text

        In addition to escaping text, unicode characters are replaced with a
        span that will display the glyph using CSS.  This is to ensure that the
        text has a consistent width.
        """
        tpl = ('<span class="u"><span class="g">&#x{0:x};</span>'
               '<span class="ns">{1}</span></span>')
        out = ''
        for c in s:
            w = utils.str_width(c)
            if unicodedata.category(c) in ('Co', 'Cn', 'So'):
                out += tpl.format(ord(c), ' ')
            elif w > 1 or ord(c) > 255:
                out += tpl.format(ord(c), ' ' * w)
            else:
                out += escape(c)
        return out

    def open_tag(self, fg, bg, seq=None, tag='span', cls=None, styles=None):
        """Opens a tag.

        This tracks how many tags are opened so they can all be closed at once
        if needed.
        """
        self._curtag_args = (fg, bg, seq, tag, cls, styles)

        classes = []
        if cls:
            classes.append(cls)

        if styles is None:
            styles = self.renderer.esc_style

        if 7 in styles:
            fg, bg = bg, fg
            classes.append('r')

        k = self.renderer.update_css('f', fg)
        if k:
            classes.append(k)
        k = self.renderer.update_css('b', bg)
        if k:
            classes.append(k)

        classes.extend(self._style_classes(styles))
        if (isinstance(fg, int) and (fg < 16 or fg == 39)) \
                and 1 in styles and 'sb' in classes:
            # Don't actually bold the basic colors since "bold" means to
            # brighten the color.
            classes.remove('sb')

        attrs = []
        if classes:
            attrs.append('class="{0}"'.format(' '.join(classes)))
        if seq:
            attrs.append('data-seq="{0}"'.format(seq))

        self.tag_stack.append(tag)
        self.chunks.append('<{tag} {attrs}>'.format(tag=tag,
                                                    attrs=' '.join(attrs)))

    def close_tag(self):
        """Closes a tag."""
        if self.tag_stack:
            tag = self.tag_stack.pop()
            self.chunks.append('</{}>'.format(tag))

    def add_cursor(self, c):
        """Append a cursor to the chunk list."""
        fg, bg, seq, tag, cls, styles = self._curtag_args
        self.open_tag(bg, fg, seq, tag, 'cu', styles)
        self.chunks.append(c)
        self.close_tag()

    def add_text(self, s):
        """Add text to the line.

        If the added text is longer than self.width, cut it and return the
        remaining text.  Since double width characters may be encountered, add
        up to the width cut the string from there.
        """
        keep = ''
        remainder = ''
        for i, c in enumerate(s):
            if ord(c) == 0x0e:
                # Shift out to alternate character set
                vt100_alt_charset['enabled'] = True
                continue
            elif ord(c) == 0x0f:
                # Shift back into standard character set
                vt100_alt_charset['enabled'] = False
                continue
            elif vt100_alt_charset['enabled']:
                x = ord(c) % 16
                y = ord(c) // 16 - 6
                if x >= 0 and x < 16 and y >= 0 and y < 2:
                    c = chr_(vt100_alt_charset['table'][x + (y * 16)])

            cw = utils.str_width(c)
            if self.length + cw > self.width:
                remainder = s[i:]
                break

            self.length += cw

            if self.col + i == self.renderer.cursor_x \
                    and self.line == self.renderer.cursor_y:
                self.chunks.append(self._escape_text(keep))
                self.add_cursor(c)
                self.renderer.column += len(keep) + 1
                self.col = self.renderer.column
                keep = ''
                continue

            keep += c

        if keep:
            self.renderer.column += len(keep)
            self.col = self.renderer.column
            self.chunks.append(self._escape_text(keep))
        return remainder

    def finalize(self):
        """Finalize the chunked line.

        Padding is added if the length is under self.width.
        """
        while self.tag_stack:
            self.close_tag()

        if self.length < self.width:
            self.open_tag(None, None, cls='ns', styles=[])
            self.add_text(' ' * (self.width - self.length))
            self.close_tag()

        text = ''.join(self.chunks)
        return '<div class="l{0}">{1}</div>'.format(self.line, text)

    __str__ = finalize
    __unicode__ = __str__

    def __hash__(self):
        return hash(tuple(self.chunks))


class Separator(object):
    def __init__(self, parent, size, vertical=True):
        self.parent = parent
        self.size = size
        self.vertical = vertical

    def __str__(self):
        if self.vertical:
            n = self.size[0]
            rep = ('<span class="u"><span class="g">&#x2500;</span>'
                   '<span class="ns"> </span></span>')
        else:
            n = self.size[1]
            rep = ('<div><span class="u"><span class="g">&#x2502;</span>'
                   '<span class="ns"> </span></span></div>')

        return '<div class="sep"><pre><span>{}</span></pre></div>' \
            .format(rep * n)


class Renderer(object):
    opened = 0
    lines = []
    css = {}
    esc_style = []

    def __init__(self, fg=(0xfa, 0xfa, 0xfa), bg=0):
        self.default_fg = fg
        self.default_bg = bg

    def rgbhex(self, c, style=None):
        """Converts a color to hex RGB."""
        if c is None:
            return 'none'
        if isinstance(c, int):
            c = color.term_to_rgb(c, style)
        return '#{:02x}{:02x}{:02x}'.format(*c)

    def update_css(self, prefix, color_code):
        """Updates the CSS with a color."""
        if color_code is None:
            return ''
        style = 'color' if prefix == 'f' else 'background-color'
        seq_style = self.esc_style
        if isinstance(color_code, int):
            if prefix == 'f' and 1 in seq_style and color_code < 8:
                color_code += 8
            else:
                seq_style = None
            key = '{0}{1:d}'.format(prefix, color_code)
        else:
            key = '{0}-rgb_{1}'.format(prefix, '_'.join(map(str_, color_code)))

        self.css[key] = ':'.join((style, self.rgbhex(color_code, seq_style)))
        return key

    def render_css(self):
        """Render stylesheet.

        If an item is a list or tuple, it is joined.
        """
        out = ''
        ctx = {
            'fonts': ','.join('"{}"'.format(x) for x in font_stack),
            'fg': self.rgbhex(self.default_fg),
            'bg': self.rgbhex(self.default_bg),
            'prefix': classname,
        }
        out = ('div.{prefix} pre {{font-family:{fonts},monospace;'
               'background-color:{bg};}}'
               'div.{prefix} pre span {{color:{fg};'
               'background-color:{bg};}}'
               'div.{prefix} pre span.r {{color:{bg};'
               'background-color:{fg};}}'
               ).format(**ctx)
        out += ('div.{prefix} pre span.cu{{color:{bg};'
                'background-color:{fg}}}').format(**ctx)

        fmt = 'div.{prefix} pre span.{cls} {{{style};}}'
        return ''.join(fmt.format(prefix=classname, cls=k,
                                  style=';'.join(v) if isinstance(v, (tuple, list)) else v)
                       for k, v in self.css.items())

    def reset_css(self):
        """Reset the CSS to the default state."""
        self.css = {
            'si': 'font-style:italic',
            'sb': 'font-weight:bold',
            'ns': [
                '-webkit-user-select:none',
                '-moz-user-select:none',
                '-ms-user-select:none',
                'user-select:none',
            ],
            'cu': [
                'color:{0}'.format(self.default_bg),
                'background-color:{0}'.format(self.default_fg),
            ],
        }

    def _render(self, s, size, max_lines=0):
        """Render the content and return a Pane instance.
        """
        cur_fg = None
        cur_bg = None
        self.esc_style = []
        pane = Pane(size, max_lines)

        prev_seq = ''
        lines = s.split('\n')
        line_c = len(lines) - 1
        for line_i, line in enumerate(lines):
            self.column = 0
            last_i = 0
            chunk = ChunkedLine(self, size[0], len(pane))
            chunk.open_tag(cur_fg, cur_bg, seq=prev_seq)
            for m in re.finditer(r'\x1b\[([^m]*)m', line):
                start, end = m.span()
                seq = m.group(1)
                c = line[last_i:start]
                last_i = end

                while True:
                    c = chunk.add_text(c)
                    if not c:
                        break
                    pane.add_line(chunk)
                    self.column = 0
                    line_c += 1
                    chunk = ChunkedLine(self, size[0], len(pane))
                    chunk.open_tag(cur_fg, cur_bg, seq=prev_seq)
                chunk.close_tag()

                cur_fg, cur_bg = color.parse_escape(seq, fg=cur_fg, bg=cur_bg,
                                                    style=self.esc_style)

                chunk.open_tag(cur_fg, cur_bg, seq=seq)
                prev_seq = seq

            c = line[last_i:]
            if c:
                if last_i == 0 and not chunk.tag_stack:
                    chunk.open_tag(cur_fg, cur_bg, seq=prev_seq)
                while True:
                    c = chunk.add_text(c)
                    if not c:
                        break
                    pane.add_line(chunk)
                    self.column = 0
                    line_c += 1
                    chunk = ChunkedLine(self, size[0], len(pane))
                    chunk.open_tag(cur_fg, cur_bg, seq=prev_seq)
                chunk.close_tag()
            if len(pane) < size[1] or (len(lines) > size[1] and len(pane) < line_c):
                pane.add_line(chunk)

        while len(pane) < size[1] or (len(lines) > size[1] and len(pane) < line_c):
            self.column = 0
            pane.add_line(ChunkedLine(self, size[0], len(pane)))
        return pane

    def _update_cursor(self, pane):
        self.cursor_x, self.cursor_y = utils.get_cursor(
            '%{}'.format(pane.identifier))

    def _render_pane(self, pane, empty=False, full=False, max_lines=0):
        """Recursively render a pane as HTML.

        Panes without sub-panes are grouped.  Panes with sub-panes are grouped
        by their orientation.
        """
        if pane.panes:
            if pane.vertical:
                self.lines.append('<div class="v">')
            else:
                self.lines.append('<div class="h">')
            for i, p in enumerate(pane.panes):
                if p.x != 0 and p.x > pane.x:
                    self.lines.append(Separator(self, p.size, False))
                if p.y != 0 and p.y > pane.y:
                    self.lines.append(Separator(self, p.size, True))
                self._render_pane(p, empty, full=full, max_lines=max_lines)

            self.lines.append('</div>')
        else:
            self.lines.append('<div id="p{}" class="pane" data-w="{}" data-h="{}">'
                              .format(pane.identifier, *pane.size))
            if not empty:
                vt100_alt_charset['enabled'] = False
                self._update_cursor(pane)
                pane = self._render(
                    utils.get_contents('%{}'.format(pane.identifier),
                                       full=full, max_lines=max_lines),
                    pane.size, max_lines=max_lines)
                self.lines.append(pane)
            else:
                self.lines.append('<pre></pre>')
            self.lines.append('</div>')

    def render_pane(self, pane, script_reload=False, full=False, max_lines=0):
        """Render a pane as HTML."""
        self.lines = []
        self.win_size = pane.size
        self.reset_css()
        self._render_pane(pane, full=full, max_lines=max_lines)
        script = ''
        template = 'static.html'
        if script_reload:
            template = 'stream.html'
        elif full and (pane.identifier == -1 or max_lines):
            template = 'scroll.html'
        return tpl.render(template, panes=''.join(str_(x) for x in self.lines),
                          css=self.render_css(), prefix=classname,
                          script=script, fg=self.rgbhex(self.default_fg),
                          bg=self.rgbhex(self.default_bg), data='',
                          interval=script_reload)

    def record(self, pane, interval, duration, window=None, session=None):
        panes = []
        frames = []
        start = time.time()
        changes = defaultdict(dict)
        frame = defaultdict(dict)
        last_frame = start
        frame_sizes = tuple()

        while True:
            try:
                n = time.time()
                if duration and n - start >= duration:
                    break

                frame.clear()
                new_pane, new_panes, new_frame_sizes = \
                    utils.update_pane_list(pane, window, session, ignore_error=True)

                if pane.dimensions != new_pane.dimensions \
                        or frame_sizes != new_frame_sizes \
                        or hash(tuple(panes)) != hash(tuple(new_panes)):
                    changes.clear()
                    self.lines[:] = []
                    self.win_size = new_pane.size
                    self._render_pane(new_pane, empty=True)
                    containers = ''.join(str_(x) for x in self.lines)
                    frames.append({
                        'delay': 0,
                        'reset': True,
                        'layout': containers,
                    })

                pane = new_pane
                panes = new_panes
                frame_sizes = new_frame_sizes

                for p in panes:
                    self.opened = 0
                    self.lines = []
                    self.win_size = p.size
                    content = utils.get_contents('%{}'.format(p.identifier))
                    if not content:
                        continue

                    self._update_cursor(p)
                    rendered = self._render(content, p.size)

                    if p.dimensions not in changes:
                        changes[p.dimensions] = {}

                    ch_pane = changes.get(p.dimensions)
                    for lc in rendered.lines:
                        line_str = str_(lc)
                        cl = ch_pane.get(lc.line)
                        if cl is None or cl != line_str:
                            ch_pane[lc.line] = line_str
                            frame[p.identifier][lc.line] = line_str

                if frame:
                    n += (time.time() - n)
                    frames.append({
                        'delay': max(0, n - last_frame),
                        'lines': frame.copy(),
                    })
                    last_frame = n
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print('Stopped recording due to an encountered error: %s' % e)
                break

        # Close the loop
        if len(frames) > 2:
            n = time.time()
            frames.append({
                'delay': n - last_frame,
            })
            frame.clear()

        str_data = []

        first, frames = frames[:50], frames[50:]
        str_data.append('<script type="text/tmux-data">{}</script>'
                        .format(''.join(utils.compress_data(json.dumps(first)))))

        for i in range(0, len(frames), 500):
            str_data.append(
                '<script type="text/tmux-data">{}</script>'
                .format(''.join(utils.compress_data(json.dumps(frames[i:i+500])))))

        return tpl.render('animation.html', panes='', css=self.render_css(),
                          prefix=classname, data='\n'.join(str_data),
                          fg=self.rgbhex(self.default_fg),
                          bg=self.rgbhex(self.default_bg))


def color_type(val):
    parts = tuple(map(int, val.split(',')))
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 3:
        return parts
    raise ValueError('Bad format')


def sil_int(val):
    """Silent int().

    Get it?
    """
    try:
        return int(val)
    except ValueError:
        return 0


def atomic_output(output, filename=None, mode=0o0644, quiet=False):
    if filename:
        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(prefix='tmp2html.',
                                              dir=os.path.dirname(filename),
                                              delete=False)
            tmp.write(output.encode('utf8'))
            tmp.flush()
            os.fsync(tmp.fileno())
        except IOError as e:
            print(e)
        except Exception:
            pass
        finally:
            if tmp:
                tmp.close()
                os.chmod(tmp.name, mode)
                os.rename(tmp.name, filename)
                if not quiet:
                    print('Wrote HTML to: {}'.format(filename))
    else:
        print(output.encode('utf8'))


def main():
    parser = argparse.ArgumentParser(description='Render tmux panes as HTML')
    parser.add_argument('target', default='', help='Target window or pane')
    parser.add_argument('-o', '--output', default='',
                        help='Output file, required with --stream')
    parser.add_argument('-m', '--mode', default='644',
                        type=lambda x: int(x, 8), help='Output file permissions')
    parser.add_argument('--light', action='store_true', help='Light background')
    parser.add_argument('--stream', action='store_true',
                        help='Continuously renders until stopped and adds a '
                        'script to auto refresh based on --interval')
    parser.add_argument('--interval', default=0.5, type=float,
                        help='Number of seconds between captures')
    parser.add_argument('--duration', default=-1, type=float,
                        help='Number of seconds to capture (0 for indefinite, '
                        '-1 to disable, ignored with --stream)')
    parser.add_argument('--fg', type=color_type, default=None,
                        help='Foreground color')
    parser.add_argument('--bg', type=color_type, default=None,
                        help='Background color')
    parser.add_argument('--full', action='store_true',
                        help='Renders the full history of a single pane')
    parser.add_argument('--history', type=int, default=0,
                        help='Specifies the maximum number of pane history '
                        'lines to include (implies --full)')
    args = parser.parse_args()

    if args.interval <= 0:
        print('Interval must be positive non-zero')
        sys.exit(1)

    window = args.target
    pane = None
    session = None
    if window.find(':') != -1:
        session, window = window.split(':', 1)

    if window.find('.') != -1:
        window, pane = window.split('.', 1)
        window = sil_int(window)
        pane = sil_int(pane)
    else:
        window = sil_int(window)

    root = utils.get_layout(window, session)
    target_pane = root
    if isinstance(pane, int):
        panes = utils.pane_list(root)
        target_pane = panes[pane]

    args.full = args.full or args.history > 0

    if args.full:
        try:
            # if target_pane.panes:
            #     raise IncompatibleOptionError('Full history can only target a '
            #                                   'pane without splits')
            if args.duration > 0:
                raise IncompatibleOptionError('Animation is not allowed in '
                                              'full history renders')
            if args.stream:
                raise IncompatibleOptionError('Streaming is not allowed in '
                                              'full history renders')
        except IncompatibleOptionError as e:
            print(e)
            sys.exit(1)

    # Dark backgrounds are very common for terminal emulators and porn sites.
    # The use of dark backgrounds for anything else just looks weird.  I was
    # able to scientifically prove this through the use of the finest
    # recreational drugs and special goggles I made out of toilet paper rolls.
    fg = (0xfa, 0xfa, 0xfa)
    bg = (0, 0, 0)

    if args.light:
        fg, bg = bg, fg

    if args.fg:
        fg = args.fg
    if args.bg:
        bg = args.bg

    r = Renderer(fg, bg)

    if args.stream:
        if not args.output:
            print('Streaming requires an output file', file=sys.stdout)
            sys.exit(1)

        print('Streaming ({0:0.2f}s) to {1}.\nPress Ctrl-C to stop.'
              .format(args.interval, args.output))
        target_panes = []
        target_frame_sizes = tuple()
        last_output = ''
        while True:
            try:
                new_pane, new_panes, new_frame_sizes = \
                    utils.update_pane_list(target_pane, window, session)
                if target_pane.dimensions != new_pane.dimensions \
                        or target_frame_sizes != new_frame_sizes \
                        or hash(tuple(target_panes)) != hash(tuple(new_panes)):
                    output = r.render_pane(target_pane, script_reload=args.interval)
                    if output != last_output:
                        last_output = output
                        atomic_output(output, args.output, quiet=True,
                                      mode=args.mode)
                time.sleep(args.interval)
            except KeyboardInterrupt:
                break

        return

    if args.duration != -1:
        if args.duration == 0:
            print('Recording indefinitely.  Press Ctrl-C to stop.')
        else:
            print('Recording for {:0.2f} seconds.  Press Ctrl-C to stop.'
                  .format(args.duration))
        output = r.record(target_pane, args.interval, args.duration, window,
                          session)
    else:
        output = r.render_pane(target_pane, full=args.full,
                               max_lines=args.history)

    atomic_output(output, args.output, mode=args.mode)
