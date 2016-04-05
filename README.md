# tmux2html

tmux2html captures full tmux windows or individual panes then parses their
contents into HTML in living ![color](https://cloud.githubusercontent.com/assets/111942/14111051/2aa0927e-f597-11e5-85d8-e529c803ec61.png).
The output can either be still snapshots, or animated sequences.

With a web server that uses gzip compression, the size over the network is
negligible for reasonably sized windows or panes.


## Examples

Some of these may be large in dimensions.  You'll need to zoom out if you want
to see all panes at once.  These are not raster graphics!

- ![Color](https://cloud.githubusercontent.com/assets/111942/14111051/2aa0927e-f597-11e5-85d8-e529c803ec61.png) `[disk: 135KB, gzip: 17KB]`: https://share.esdf.io/FGlV4sufpt/color.html
- Single Pane `[disk: 65KB, gzip: 6KB]`: https://share.esdf.io/saRkuNriJt/single.html
- Full Window (Big) `[disk: 134KB, gzip: 11KB]`: https://share.esdf.io/h5lGMPdcZF/full.html
- Animated `[disk: 638KB, gzip: 262KB]`: https://share.esdf.io/3qdZm2szkN/animated.html
- Partially Animated (Big) `[disk: 192KB, gzip: 79KB]`: https://share.esdf.io/EJHQXoIQDT/partial-animated.html
  (Only some panes are animating)

If you decide to look at the telnet animations yourself and don't know how to
exit, use `Ctrl-]` then type `quit`.  For the Star Wars animation, press
`Ctrl-]<enter>` to get the prompt.


## Rationale

This was a weekend project I made for fun and I have no particular use for it
beyond annoying my friends about how bad they should feel for not using tmux.
I also thought it would be neat to have a render of my sessions that didn't
result in an image using some crummy font on a headless server.

I suppose you can use cron to capture screens and display it on your website,
or use it to create terminal snippets for your blog.  You could also load a
pane render in elinks within your coworker's session.  The only limit is your
imagination, my friend. :sparkles:


## Requirements

- tmux 1.8
- Python 2.7 or 3.4 (could be wrong since it's not tested in lower versions)


## Installation

```shell
pip install tmux2html
```


## Usage

```shell
tmux2html 4 -o window_5_in_current_session.html
tmux2html .0 -o first_pane_in_current_window.html
tmux2html other:1.2 -o second_window_third_pane_in_other_session.html
```

### Command Line Options

- `target` (positional) - Target window or pane.  Uses tmux's target syntax, but
  always 0-indexed.  (e.g. `sess:1.2` - Session - sess, Window 2, Pane 3.
  Default target is window.)
- `-o`, `--output` -  Output file.  Prints to stdout if omitted.
- `-m`, `--mode` -  Output file permissions.  Default - 644
- `--light` -  Light background.
- `--interval` -  Number of seconds between captures.
- `--duration` -  Number of seconds to capture.  0 for indefinite recording, -1
  to disable.
- `--stream` -  Continuously renders until stopped and adds a script to auto
  refresh based on `--interval`.  See the notes below for more info.
- `--fg` -  Foreground color.  Can be a color index or R,G,B
- `--bg` -  Background color.  Can be a color index or R,G,B
- `--full` - Renders the full history of a single pane
- `--history` - Specifies the maximum number of pane history lines to include
  (implies `--full`)


## Limitations

- The cursor is not displayed.
- Basic colors will not match your terminal's configured colors.
- Animations aren't perfect with a lot of splits and fast resizing.
- Animations won't capture scrolling the pane's history (selection mode).
- In animations, a pane is updated with the full pane's content.
- Zoomed panes will ruin all the fun.
- Your imagination :stars:


## Notes

- Still captures are plain HTML and CSS.
- Animations use Javascript.
- To keep the size reasonable with animations,
  [pako](https://github.com/nodeca/pako) is used to inflate the gzipped frame
  contents.  Combined with decompression of frame content, the animations will
  use a fair amount of CPU.  So, you shouldn't run animations indefinitely on
  your low performance or battery operated fun machines.
- `--stream` doesn't actually "stream", per se.  It keeps writing to the same
  file and adds a script that reloads the contents.  This can be used to
  have a live feed of a window or pane.  However, it's not elegant.  If you set
  the interval to too low, your might unintentionally DDoS your own web server.
  Caveat Emptor.
- The font stack includes [Powerline](https://github.com/powerline/fonts) and
  [Nerd](https://github.com/ryanoasis/nerd-fonts) fonts because I'm pedantic
  and want to see those fancy glyphs.  It falls back to `monospace` if you
  don't have any of those fonts installed.  The caveat: if you have more than
  one of those fonts installed, the first one in the font stack might not be
  your favorite and you'll be forced to set your monitor on fire and buy a new
  one.


## To Do

- If there's practical use for animations in the future, only lines that are
  different should be updated to keep the size low.


## Similar Projects

- [gotty](https://github.com/yudai/gotty) - Share your terminal as a web
  application
- [asciinema](https://github.com/asciinema/asciinema) - Terminal session
  recorder


## License

- tmux2html: MIT
- [pako](https://github.com/nodeca/pako): MIT
