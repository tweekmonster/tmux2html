from __future__ import print_function

import re
import argparse
from string import Template

from . import color, utils

try:
    from html import escape
except ImportError:
    from cgi import escape


tpl = Template('''
<!doctype html>
<head>
  <style>
    div.tmux {
      display: inline-block;
    }
    div.tmux pre {
      margin: 0;
      padding: 0;
    }
    div.tmux pre span.u {
      position: relative;
      display: inline-block;
      color: inherit;
      background-color: transparent;
    }
    div.tmux pre span.u:after {
      content: attr(data-glyph);
      display: block;
      position: absolute;
      top: 0;
      left: 0;
    }
    $css
  </style>
</head>
<body>
<div class="tmux">$pre</div>
</body>
'''.strip())


class Renderer(object):
    default_fg = (255, 255, 255)
    default_bg = (0, 0, 0)
    opened = 0
    chunks = []
    css = {}
    esc_style = []

    def rgbhex(self, c):
        if not c:
            return 'none'
        return '#{:02x}{:02x}{:02x}'.format(*c)

    def parse_styles(self, styles):
        out = ''
        if 1 in styles:
            out += 'font-weight:bold;'
        if 3 in styles:
            out += 'font-style:italic;'
        if 4 in styles:
            out += 'text-decoration:underline;'
        return out

    def update_css(self, prefix, color_code):
        if color_code is None:
            return ''

        if prefix == 'fg':
            style = 'color'
        else:
            style = 'background-color'

        if isinstance(color_code, int):
            if prefix == 'fg' and 1 in self.esc_style and color_code < 8:
                color_code += 8
            c = self.rgbhex(color.term_to_rgb(color_code, self.esc_style))
            key = '{0}-{1:d}'.format(prefix, color_code)
            self.css[key] = '{0}: {1};'.format(style, c)
        else:
            key = '{0}-rgb_{1}'.format(prefix, '_'.join(map(str, color_code)))
            self.css[key] = '{0}: {1};'.format(style, self.rgbhex(color_code))
        return key

    def render_css(self):
        out = ''
        out += 'div.tmux pre span {{ color: {0}; background-color: {1}; }}\n'.format(self.rgbhex(self.default_fg), self.rgbhex(self.default_bg))
        for k, v in self.css.items():
            out += 'div.tmux pre span.{0} {{ {1} }}\n'.format(k, v)
        return out

    def open(self, fg, bg, seq=None, tag='span'):
        classes = []
        if 7 in self.esc_style:
            fg, bg = bg, fg

        k = self.update_css('fg', fg)
        if k:
            classes.append(k)
        k = self.update_css('bg', bg)
        if k:
            classes.append(k)

        self.opened += 1
        attrs = []
        if classes:
            attrs.append('class="{0}"'.format(' '.join(classes)))
        styles = self.parse_styles(self.esc_style)
        if styles:
            attrs.append('style="{0}"'.format(styles))
        if seq:
            attrs.append('data-seq="{0}"'.format(seq))
        html = '<{tag} {attrs}>'.format(tag=tag, attrs=' '.join(attrs))
        self.chunks.append(html)

    def close(self, tag='span', closeall=False):
        if self.opened > 0:
            if closeall:
                self.chunks.extend(['</{}>'.format(tag)] * self.opened)
                self.opened = 0
            else:
                self.opened -= 1
                self.chunks.append('</{}>'.format(tag))

    def format_text(self, s):
        s = escape(s)
        s = re.sub(r'([\u0080-\uffff])', r'<span class="u" data-glyph="\1"> </span>', s)
        return s

    def wrap(self, line, length, maxlength):
        while length > maxlength:
            cut = maxlength - length
            self.chunks.append(self.format_text(line[:cut]))
            self.chunks.append('\n')
            line = line[cut:]
            length = len(line)
        return length, line

    def render(self, s, size):
        self.opened = 0
        self.chunks = ['<pre>']
        cur_fg = None
        cur_bg = None
        self.esc_style = []

        for line in s.split('\n'):
            last_i = 0
            line_l = 0
            for m in re.finditer(r'\x1b\[([^m]*)m', line):
                start, end = m.span()
                c = line[last_i:start]

                if c and last_i == 0 and not self.opened:
                    self.open(cur_fg, cur_bg)

                c_len = len(c)
                line_l += c_len
                line_l, c = self.wrap(c, line_l, size[0])

                if c:
                    self.chunks.append(self.format_text(c))

                if last_i == 0:
                    self.close()

                last_i = end

                cur_fg, cur_bg = color.parse_escape(m.group(1), fg=cur_fg,
                                                    bg=cur_bg,
                                                    default_fg=self.default_fg,
                                                    default_bg=self.default_bg,
                                                    style=self.esc_style)

                self.close()
                self.open(cur_fg, cur_bg, m.group(1))

            c = line[last_i:]
            c_len = len(c)
            line_l += c_len
            if not self.opened:
                self.open(cur_fg, cur_bg)

            line_l, c = self.wrap(c, line_l, size[0])
            pad = ' ' * (size[0] - line_l)

            if c:
                self.chunks.append(self.format_text(c))
            self.close(closeall=True)

            if pad:
                self.open(None, None)
                self.chunks.append(pad)
                self.close()
            self.chunks.append('\n')

        self.chunks.append('</pre>')
        return tpl.substitute(pre=''.join(self.chunks), css=self.render_css())


def main():
    parser = argparse.ArgumentParser(description='Render tmux panes as HTML')
    parser.add_argument('-t', '--target', help='tmux pane target')
    args = parser.parse_args()
    term_content = utils.get_contents(args.target)
    term_size = utils.get_panesize(args.target)
    r = Renderer()
    with open('test.html', 'w') as fp:
        fp.write(r.render(term_content, term_size))
