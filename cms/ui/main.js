
var IE = document.all?true:false;


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


/*
* Keep mouse coordinates
*
* http://javascript.internet.com/page-details/mouse-coordinates.html
$*/
if (!IE) {
  document.captureEvents(Event.MOUSEMOVE);
}

/*document.onmousemove = getMouseXY;*/

var tempX = 0;
var tempY = 0;
function getMouseXY(e) {
  if (IE) { // grab the x-y pos.s if browser is IE
    tempX = event.clientX + document.body.scrollLeft;
    tempY = event.clientY + document.body.scrollTop;
  }
  else {  // grab the x-y pos.s if browser is NS
    tempX = e.pageX;
    tempY = e.pageY;
  }  
  if (tempX < 0) {
    tempX = 0;
  }
  if (tempY < 0) {
    tempY = 0;
  }
  /*  document.Show.MouseX.value = tempX;
      document.Show.MouseY.value = tempY;*/
  return true;
}



/* TIPS */
function show_tip() {
  tip = document.getElementById('tip_body');
  tip.style.visibility = 'visible';
}

function hide_tip() {
  tip = document.getElementById('tip_body');
  tip.style.visibility = 'hidden';
}


/* REMOVE CONFIRMATION */
function confirmation()
{
if (!confirm ("Delete this objet, are you sure?"))
return false;
}


