/*
 * This function will not return until (at least)
 * the specified number of milliseconds have passed.
 * It does a busy-wait loop.
 *
 * http://www.faqts.com/knowledge_base/view.phtml/aid/1602
 */
function pause(numberMillis) {
  var now = new Date();
  var exitTime = now.getTime() + numberMillis;
  while (true) {
    now = new Date();
    if (now.getTime() > exitTime)
      return;
  }
}

/* REMOVE CONFIRMATION */
/* XXX needs translation */
function confirmation()
{
  if (!confirm ("Delete this objet, are you sure?"))
    return false;
}

function focus(id) {
  var element = document.getElementById(id);
  element.focus();
}

function hide(id) {
  var element = document.getElementById(id);
  element.style.display = 'none'; 
}

function show(id) {
  element = document.getElementById(id);
  element.style.visibility = 'block';
}
