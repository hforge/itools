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
  element.style.display = 'none'; 
}

function show(id) {
  element = document.getElementById(id);
  element.style.visibility = 'block';
}

function setTabHover(element) {
  if (element.className.indexOf("tab_active") != -1) {
    /* the "already_active" class doesn't exist, just a flag */
    element.className = "tab_active already_active";
  } else {
    element.className ="tab_active";
  }
}

function setTabOut(element) {
  /* the "already_active" class doesn't exist, just a flag */
  if (element.className.indexOf("already_active") != -1) {
    element.className = "tab_active";
  } else {
    element.className = "";
  }
}

function setTabsHover() {
  if (!document.all) {
    return;
  }
  ids = new Array("tabs", "subtabs");
  for (i = 0; i < ids.length; i++) {
    id = ids[i];
    lis = document.getElementById(id).getElementsByTagName("li");
    for (j = 0; j < lis.length; j++) {
      li = lis[j];
      li.onmouseover = function() {
        setTabHover(this);
      }
      li.onmouseout = function() {
        setTabOut(this);
      }
    }
  }
}

addEvent(window, 'load', setTabsHover);
