
setTimeout(function() {
  const timestamp = Date.now();
  window.location.href = '/?ts=' + timestamp;
}, 500);
