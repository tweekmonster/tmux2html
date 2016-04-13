var loadData = require('./lib/data');
var raf = require('raf');
var ease = require('eases/quint-out');

function setupPane(pane) {
  var hunks = pane.querySelectorAll('script[type="text/tmux-data"]');
  var lines = [];
  for (var i = 0; i < hunks.length; i++) {
    var data = loadData(hunks[i].textContent || hunks[i].innerText);
    lines.push.apply(lines, data.split('\n'));
  }

  var height = parseInt(pane.dataset.h, 10);
  var pre = pane.querySelector('pre');
  var top = lines.length - height;
  var maxTop = top;
  var lineHeight = pre.childNodes[0].clientHeight;
  var touchStart = 0;
  var touchLineStart = 0;

  function cleanup() {
    var remove = pane.querySelectorAll('pre > div.hs');
    for (var i = 0; i < remove.length; i++) {
      pre.removeChild(remove[i]);
    }
  };

  function setScrollPosition(line) {
    var line = Math.max(0, Math.min(maxTop, line));
    if (line == top) {
      return;
    }

    var histMax = lines.length - height;
    var histPos = histMax - line;
    if (histPos === 0) {
      pre.dataset.sp = '';
    } else {
      pre.dataset.sp = '[' + histPos + '/' + histMax + ']';
    }
    top = line;
    var view = lines.slice(line, line + height);
    var d = document.createElement('div');

    // Only hide the old nodes since touchmove resets if an element is removed.
    for (var i = 0; i < pre.childNodes.length; i++) {
      pre.childNodes[i].classList.add('hs');
    }

    for (var i = 0; i < view.length; i++) {
      d.innerHTML = view[i];
      pre.appendChild(d.firstChild);
    }

    if (touchStart === 0) {
      cleanup();
    }
  }

  pane.addEventListener('mousewheel', function(e) {
    e.preventDefault();
    var delta = e.deltaY / lineHeight;
    if (Math.round(delta) === 0) {
      if (delta < 0) {
        delta = -1;
      } else {
        delta = 1;
      }
    }

    setScrollPosition(top + Math.round(delta));
  }, false);


  var frames = 10;
  var frame = frames;
  var frameDelta = 0;
  var scrollFactor = 0;
  var scrollOrigin = 0;
  var lastPos = 0;
  var touchStartTime = 0;
  var inertialScrollRunning = false;

  function inertialScroll() {
    if (touchStart !== 0) {
      return;
    }
    var m = 1 * ease(frame / frames);
    frameDelta += scrollFactor * (1 - m);
    setScrollPosition(scrollOrigin + Math.round(frameDelta));

    frame++
    if (frame < frames && top > 0 && top < maxTop) {
      raf(inertialScroll);
    } else {
      inertialScrollRunning = false;
      frameDelta = 0;
      scrollFactor = 0;
    }
  }

  var lastTouch = 0;
  pane.setAttribute('onclick', 'void(0)');
  pane.addEventListener('touchstart', function(e) {
    if (e.touches.length < 2) {
      return;
    }
    lastTouch = touchStartTime = new Date();
    lastPos = e.changedTouches[0].clientY;
    touchStart = Math.round(lastPos / lineHeight);
    touchLineStart = top;
    e.preventDefault();
  }, false);

  pane.addEventListener('touchend', function(e) {
    touchStart = 0;
    cleanup();
    if (((new Date()) - touchStartTime) / 1000 < 0.3) {
      scrollOrigin = top;
      frame = 0;
      frameDelta = 0;
      if (!inertialScrollRunning) {
        inertialScrollRunning = false;
        inertialScroll();
      }
    }
    touchStartTime = 0;
    e.preventDefault();
  }, false);

  pane.addEventListener('touchmove', function(e) {
    if (touchStart) {
      var n = new Date();
      var pos = e.changedTouches[0].clientY;
      var velocity = Math.abs((lastPos - pos) * ((lastTouch - n) / 1000));
      lastPos = pos;
      lastTouch = n;
      delta = touchStart - (pos / lineHeight);
      if (((scrollFactor < 0) != (delta < 0)) || (Math.abs(delta) < height / 2 && (n - touchStartTime) / 1000 >= 0.3)) {
        // If the signs are different or it's been too long since starting
        // touch events
        scrollFactor = delta;
      } else if (delta) {
        // Increase scroll amount
        scrollFactor += delta * velocity;
      }
      setScrollPosition(touchLineStart + Math.round(delta));
      e.preventDefault();
      e.stopPropagation();
    }
  }, false);
}


panes = document.querySelectorAll('.pane');
for (var i = 0; i < panes.length; i++) {
  setupPane(panes[i]);
}
