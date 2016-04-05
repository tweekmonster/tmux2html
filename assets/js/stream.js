var interval = $interval;

function parse(xhr) {
  if (this.readyState === 4 && this.status === 200) {
    var m = /<div class="$prefix">([\s\S]+)<\/div>/.exec(this.responseText);
    if (m) {
      document.querySelector('div.$prefix').innerHTML = m[1];
    }

    m = /<style>([\s\S]+)<\/style>/.exec(this.responseText);
    if (m) {
      document.querySelector('style').innerText = m[1];
    }

    setTimeout(reload, interval * 1000);
  }
}

function reload() {
  var r = new XMLHttpRequest();
  r.addEventListener('readystatechange', parse);
  r.open('GET', location.href);
  r.send();
}

setTimeout(reload, interval * 1000);
