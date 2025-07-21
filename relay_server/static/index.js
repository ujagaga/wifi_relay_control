
function addTimestampToLinks() {
  const timestamp = new Date().getTime();

  const links = document.querySelectorAll('a.big_btn');

  links.forEach(function(link) {
    const href = link.getAttribute('href');

    if (href.includes('?')) {
      // If there's a query string, append the timestamp with an '&'
      link.setAttribute('href', href + '&timestamp=' + timestamp);
    } else {
      // If there's no query string, append the timestamp with a '?'
      link.setAttribute('href', href + '?timestamp=' + timestamp);
    }
  });
}



document.addEventListener('DOMContentLoaded', () => {
    addTimestampToLinks();
    document.querySelectorAll('.ping_time').forEach(span => {
    const iso = span.dataset.iso;
    if (iso) {
      const localTime = new Date(iso).toLocaleString(undefined, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
      span.textContent = localTime;
    }
  });
});