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

/**
  http://ejohn.org/projects/flexible-javascript-events/
  */
function addEvent( obj, type, fn ) {
  if ( obj.attachEvent ) {
    obj['e'+type+fn] = fn;
    obj[type+fn] = function(){obj['e'+type+fn]( window.event );}
    obj.attachEvent( 'on'+type, obj[type+fn] );
  } else
    obj.addEventListener( type, fn, false );
}

function removeEvent( obj, type, fn ) {
  if ( obj.detachEvent ) {
    obj.detachEvent( 'on'+type, obj[type+fn] );
    obj[type+fn] = null;
  } else
    obj.removeEventListener( type, fn, false );
}
/* */

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
  if (element) {
    element.style.visibility = 'hidden'; 
  }
}

function show(id) {
  element = document.getElementById(id);
  if (element) {
    element.style.visibility = 'visible';
  }
}

