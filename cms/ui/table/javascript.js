function trim(s) {
    return s.replace(/^\s+/, '').replace(/\s+$/, '');
}

function str_to_date(str) {
    // format : 2007-08-27
    var year = str.substring(0, 4);
    var month = str.substring(5, 7);
    var day = str.substring(8);

    var d = new Date();
    d.setFullYear(year);
    d.setMonth(month - 1); // 0 - 11
    d.setDate(day);
    return d;
}

function tableFlatCallback(cal) {
    var MA = cal.params.multiple;
    // update only for flat click on date event or popup calendar onClose
    if (cal.dateClicked || cal.params.flat == null || cal.params.electric) {
        if (cal.multiple) {
            // Reset the "MA", in case one triggers the calendar again (popup only)
            if ( cal.params.flat == null )
               MA.length = 0;
            // walk the calendar multiple dates selection hash
            var content = '';
            for (var i in cal.multiple) {
                var d = cal.multiple[i];
                // sometimes the date is not actually selected, that is why we need to check.
                if (d) {
                    // we will display all selected dates in the element having the id "output".
                    content += d.print(cal.dateFormat) + '\n';
                    // and push it in the "MA", in case one triggers the calendar again (popup only)
                    if ( cal.params.flat == null )
                        MA[MA.length] = d;
                }
            }
            cal.params.displayArea.value = content;
        }
        else {
            cal.params.displayArea.value = cal.date.print(cal.dateFormat);
        }
    }
    if ( cal.params.flat == null )
            cal.hide();
    return true;
}

function tableFlatOuputOnBlur(caller, cal) {
    var cvalue = trim(caller.value);
    var tab = [];
    var reg = new RegExp("\n+", "g");
    var tmp = cvalue.split(reg);
    tmp.sort();
    caller.value = tmp.join('\n');
    for (var i in tmp) {
        tab.push(str_to_date(tmp[i]));
    }
    cal.update(tab);
}
