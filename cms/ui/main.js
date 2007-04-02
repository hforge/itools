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

/* X & Y Coords */

function getPosX(obj)
{
	var curleft = 0;
	if (obj.offsetParent) {
		while (obj.offsetParent) {
			curleft += obj.offsetLeft;
			obj = obj.offsetParent;
		}
	}
	else if (obj.x) {
		curleft += obj.x;
    }
	return curleft;
}

function getPosY(obj)
{
	var curtop = 0;
	if (obj.offsetParent) {
		while (obj.offsetParent) {
			curtop += obj.offsetTop;
			obj = obj.offsetParent;
		}
	}
	else if (obj.y) {
		curtop += obj.y;
    }
	return curtop;
}

/* Width & Height */

function getWidth(obj) {
  if (obj.currentStyle) {
    var y = obj.currentStyle["width"];
  }
  else if (window.getComputedStyle) {
    var y = document.defaultView.getComputedStyle(obj,null).getPropertyValue("width");
  }
  return parseInt(y);
}

function setWidth(obj, width) {
  obj.style.width = width + "px";
}

function getHeight(obj) {
  if (obj.currentStyle) {
    var y = obj.currentStyle["height"];
  }
  else if (window.getComputedStyle) {
    var y = document.defaultView.getComputedStyle(obj,null).getPropertyValue("height");
  }
  return parseInt(y);
}

function setHeight(obj, height) {
  obj.style.height = height + "px";
}

/* Browse: select all/none */
function select_checkboxes(form_id, checked) {
  var form = document.getElementById(form_id);
  var checkboxes = form.ids;
  for (i = 0; i < checkboxes.length; i++) {
    checkboxes[i].checked = checked;
  }
  return false;
}
