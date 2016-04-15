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
  var speed = 1;

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
        if (!container) {
          continue;
        }
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
      var n = nextDelay() * 1000;
      if (n) {
        var adj = (new Date()) - d;
        timerID = setTimeout(nextFrame, (n * speed) - adj);
      }
    }
  }

  decompress(nextFrame);

  this.setSpeedMultiplier = function(d) {
    // This is a multiplier!
    // 0.5 doubles the speed
    // 1 is normal speed
    // 2 is half the speed
    // etc.
    if (d <= 0) {
      return;
    }
    speed = d;
  };

  this.stop = function() {
    clearInterval(timerID);
  };

  this.resume = function() {
    nextFrame();
  };

  this.next = function(n) {
    // Skips n frames.
    this.stop();

    if (isNaN(n) || !n || n < 1) {
      n = 1;
    }

    while (n > 0) {
      nextFrame(true);
      n--;
    }
  };

  // Moving backwards is currently not supported due to how frames are built
  // from the previous frames.  This would need refactoring to add the ability
  // to move backwards.
})();
