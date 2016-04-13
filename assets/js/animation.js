var loadData = require('./lib/data');
var init = false;
var frame = 0;
var frames = [];
var timerID = 0;

function decompress(cb) {
  var frag = document.querySelector('script[type="text/tmux-data"]');
  if (!frag) {
    return;
  }
  frames.push.apply(frames, JSON.parse(loadData(frag.textContent || frag.innerText)));
  frag.parentNode.removeChild(frag);
  if (!init) {
    init = true;
    cb();
  }
  setTimeout(decompress, 0);
}

window.tmux = new (function() {
  function nextDelay() {
    if (frames.length < 3) {
      return 0;
    }

    var f = frame;
    var g = 0;
    while (g < 4) {
      g++;
      var next = frames[f % frames.length];
      if (next.delay) {
        return next.delay;
      }
      f++;
    }
    return 0;
  }

  function nextFrame(no_advance) {
    var d = new Date();
    clearInterval(timerID);
    var fr = frames[frame % frames.length];
    frame++;
    if (fr.reset) {
      document.querySelector('.$prefix').innerHTML = fr.layout;
      return nextFrame(no_advance);
    }

    if (fr.lines) {
      for (var id in fr.lines) {
        var container = document.querySelector('#p' + id + ' > pre');
        if (!container.childNodes.length) {
          var html = '';
          for (var l in fr.lines[id]) {
            html += fr.lines[id][l];
          }
          container.innerHTML = html;
        } else {
          for (var l in fr.lines[id]) {
            container.childNodes[l].outerHTML = fr.lines[id][l];
          }
        }
      }
    }

    if (!!!no_advance && frames.length > 2) {
      var n = nextDelay();
      if (n) {
        var adj = (new Date()) - d;
        timerID = setTimeout(nextFrame, (n * 1000) - adj);
      }
    }
  }

  decompress(nextFrame);

  this.stop = function() {
    clearInterval(timerID);
  };

  this.resume = function() {
    nextFrame();
  };

  this.next = function() {
    this.stop();
    nextFrame(true);
  };
})();
