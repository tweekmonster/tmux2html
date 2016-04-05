var loadData = require('./lib/data');

function setupPane(pane) {
  var hunks = pane.querySelectorAll('script[type="text/tmux-data"]');
  var lines = [];
  for (var i = 0; i < hunks.length; i++) {
    var data = loadData(hunks[i].innerText);
    lines.push.apply(lines, data.split('\n'));
  }

  var height = parseInt(pane.dataset.h, 10);
  var pre = pane.querySelector('pre');
  var top = lines.length - height;
  var maxTop = top;
  var lineHeight = pre.childNodes[0].clientHeight;

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
    var line = Math.max(0, Math.min(maxTop, top + Math.round(delta)));
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
    console.log('height', height, 'start', line, 'end', line + height, 'view len', view.length);

    for (var i = 0; i < view.length; i++) {
      pre.childNodes[i].outerHTML = view[i];
    }
  });
}


panes = document.querySelectorAll('.pane');
for (var i = 0; i < panes.length; i++) {
  setupPane(panes[i]);
}
