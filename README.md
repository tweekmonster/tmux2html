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
- Single Pane `[disk: 124KB, gzip: 13KB]`: https://share.esdf.io/oby611JQvB/single.html
- Full Window (Big) `[disk: 237KB, gzip: 21KB]`: https://share.esdf.io/9t7tgDC4Gf/full.html
- Animated `[disk: 204KB, gzip: 146KB]`: https://share.esdf.io/sVu5q1xFk9/animated.html
- Partially Animated (Big) `[disk: 122KB, gzip: 89KB]`: https://share.esdf.io/UNoltIEHt4/partial-animated.html
  (Only some panes are animating)
- Scrollable pane history `[disk: 83KB, gzip: 47KB]`: https://share.esdf.io/sEDNecDCat/scroll.html
  (Scroll with the mouse wheel, or two fingers on a touch screen.)
- Complete pane history `[disk: 63KB, gzip: 18KB]`: https://share.esdf.io/bvn100jhi7/history.html
- Over kill animation `[disk: 679KB, gzip: 516KB]`: https://share.esdf.io/eSZQheewUL/absurd-animation.html
  (This animation is recorded using a 10ms interval.  It will not be great on mobile devices.)
- "Streaming": https://share.esdf.io/log.html
  (This displays the HTTP log for the links above.)

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


### What people think of tmux2html

> tmux2html 便利そう。

  — [@nakamuray](https://twitter.com/nakamuray/status/717620065303015425)

> aaaaoooooo

  — [@l4utert](https://twitter.com/l4utert/status/718046015908155393)

> 9:39:46 PM Jef Myers: what the fuck is tmux?

  — Jef Myers


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
- ~~Animations won't capture scrolling the pane's history (selection mode).~~
  Scrolling in the pane's history is now recorded in animations.
- ~~In animations, a pane is updated with the full pane's content.~~  Only the
  changed lines are updated on a per-pane basis.
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

- ~~If there's practical use for animations in the future, only lines that are
  different should be updated to keep the size low.~~
- Tell people to follow me on Twitter
  ([@cloudsiphon](https://twitter.com/cloudsiphon)) if they would like to stay
  up to date on tmux2html, but don't be pushy about it.


## Similar Projects

- [gotty](https://github.com/yudai/gotty) - Share your terminal as a web
  application
- [asciinema](https://github.com/asciinema/asciinema) - Terminal session
  recorder


## License

- tmux2html: MIT
- [pako](https://github.com/nodeca/pako): MIT
