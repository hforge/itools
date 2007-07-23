
function update_dtstart(cal) {
    var date = cal.date;
    var field = document.getElementById("DTSTART_year");
    field.value = date.print("%Y");
    var field = document.getElementById("DTSTART_month");
    field.value = date.print("%m");
}

function update_dtend(cal) {
    var date = cal.date;
    var field = document.getElementById("DTEND_year");
    field.value = date.print("%Y");
    var field = document.getElementById("DTEND_month");
    field.value = date.print("%m");
}

