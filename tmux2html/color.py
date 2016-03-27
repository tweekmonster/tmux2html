_colors_8 = [
    (0x00, 0x00, 0x00),
    (0x80, 0x00, 0x00),
    (0x00, 0x80, 0x00),
    (0x80, 0x80, 0x00),
    (0x00, 0x00, 0x80),
    (0x80, 0x00, 0x80),
    (0x00, 0x80, 0x80),
    (0x80, 0x80, 0x80),
]

_cube_6 = (0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff)


def term_to_rgb(n, style):
    '''Get the R/G/B values for a terminal color index

    0 - 15 are the basic colors
    16 - 231 are the 6x6 RGB colors
    232 - 255 are the gray scale colors
    '''
    if n < 16:
        rgb = _colors_8[n % 8]
        if n > 7 or 1 in style:
            return tuple(map(lambda i: min(255, i + 0x80), rgb))
        return rgb

    if n < 232:
        n -= 16
        if n == 0:
            return (0x00, 0x00, 0x00)
        return (_cube_6[n // 36], _cube_6[(n // 6) % 6], _cube_6[n % 6])

    n -= 232
    c = 8 + (n * 10)
    return (c, c, c)


def _parse_colors(parts):
    type_ = next(parts)
    if type_ == 2:
        return (
            int(next(parts)),
            int(next(parts)),
            int(next(parts)),
        )
    elif type_ == 5:
        return int(next(parts))


def _iter_escape(s):
    for p in s.split(';'):
        try:
            yield int(p)
        except ValueError:
            print(p)


def parse_escape(s, fg=None, bg=None, style=None, default_fg=(255, 255, 255),
                 default_bg=(0, 0, 0)):
    if style is None:
        style = []

    if not s:
        return (None, None)

    parts = _iter_escape(s)
    for p in parts:
        if p == 38:
            fg = _parse_colors(parts)
        elif p == 48:
            bg = _parse_colors(parts)
        elif p == 39:
            fg = None
        elif p == 49:
            bg = None
        else:
            if p >= 30 and p <= 37:
                fg = p - 30
            elif p >= 40 and p <= 47:
                bg = p - 40
            elif p not in style:
                if p == 0:
                    style[:] = []
                else:
                    style.append(p)

    return (fg, bg)
