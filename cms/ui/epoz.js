
function InitDocument(iframe) {
    fieldId = iframe.id.slice(IFramePrefixLength);
    ta = document.getElementById(fieldId);
    iframe.contentWindow.document.id = DocPrefix + fieldId;
    addListener(iframe, "click", HandleEpozRedirect);
    form = retrieveForm(ta);
    form.onsubmit=SyncEpoz;
    if (browser.isGecko) {
        scriptExpr = 'EnableDesignMode("' + iframe.id + '");';
        window.setTimeout(scriptExpr, 10);
    }
}


// Epoz - a cross-browser-wysiwyg-editor for Zope
// Copyright (C) 2005 Maik Jablonski (maik.jablonski@uni-bielefeld.de)

// Just to prevent typos when fetching the Epoz-IFrame...

var Epoz = "EpozEditor";

// Speed-Up-Storage for document.getElementById(Epoz);

var EpozElement;
var EpozTextArea;

// Global storages

var form_data;  // the document-data
var form_name;  // the name of the form-element
var form_path;  // path to buttons, font-selectors, ...
var form_toolbox; // path to optional toolbox
var form_area_style; // css-definition for wysiwyg-area
var form_button_style; // css-definition for buttons
var form_css; // css-style for iframe
var form_customcss; // customized css-style for iframe
var form_charset; // charset for iframe
var form_pageurl; // real url for the edited page


// Returns the current HTML.

function GetHTML(source_mode) {
    if (source_mode == null) {
        source_mode = document.getElementById('EpozViewMode').checked;
    }

    if (source_mode) {
        return EpozTextArea.value;
    } else {
        try {
            return EpozElement.contentWindow.document.body.innerHTML;
        } catch (e) {
            return EpozElement.value;
        }
    }
}

// Here are the definitions for the control-and-format-functions

// Format text with RichText-Controls

function FormatText(command, option) {
    EpozElement.contentWindow.focus();

    // Mozilla inserts css-styles per default

  if (browser.isGecko) {
      EpozElement.contentWindow.document.execCommand('useCSS',false, true);
    }

    EpozElement.contentWindow.document.execCommand(command, false, option);
}


// Insert arbitrary HTML at current selection

function InsertHTML(html) {

    EpozElement.contentWindow.focus();

    if (browser.isIE5up) {
        selection = EpozElement.contentWindow.document.selection;
        range = selection.createRange();
        try {
            range.pasteHTML(html);
        } catch (e) {
            // catch error when range is evil for IE
        }
    } else {
        selection = EpozElement.contentWindow.window.getSelection();
        EpozElement.contentWindow.focus();
        if (selection) {
            range = selection.getRangeAt(0);
        } else {
            range = EpozElement.contentWindow.document.createRange();
        }

        var fragment = EpozElement.contentWindow.document.createDocumentFragment();
        var div = EpozElement.contentWindow.document.createElement("div");
        div.innerHTML = html;

        while (div.firstChild) {
            fragment.appendChild(div.firstChild);
        }

        selection.removeAllRanges();
        range.deleteContents();

        var node = range.startContainer;
        var pos = range.startOffset;

        switch (node.nodeType) {
            case 3:
                if (fragment.nodeType == 3) {
                    node.insertData(pos, fragment.data);
                    range.setEnd(node, pos + fragment.length);
                    range.setStart(node, pos + fragment.length);
                } else {
                    node = node.splitText(pos);
                    node.parentNode.insertBefore(fragment, node);
                    range.setEnd(node, pos + fragment.length);
                    range.setStart(node, pos + fragment.length);
                }
                break;

            case 1:
                node = node.childNodes[pos];
                node.parentNode.insertBefore(fragment, node);
                range.setEnd(node, pos + fragment.length);
                range.setStart(node, pos + fragment.length);
                break;
        }
        selection.addRange(range);
    }
}


// Create an anchor - no browser supports this directly

function CreateAnchor(name) {
  name = prompt(EpozLang["EnterAnchorName"], "");
  if (name) {
    anchorhtml = '<a name="' + name + '" title="' + name + '"></a>';
    InsertHTML(anchorhtml);
  }
}


// Create a Hyperlink - IE has its own implementation

function CreateLink(URL) {
    if (browser.isIE5up == false && ((URL == null) || (URL == ""))) {
        URL = prompt(EpozLang["EnterLinkURL"], "");

        if ((URL != null) && (URL != "")) {
            EpozElement.contentWindow.document.execCommand("CreateLink",false,URL)
        } else {
            EpozElement.contentWindow.document.execCommand("Unlink",false, "")
        }
    } else {
        EpozElement.contentWindow.document.execCommand("CreateLink",false,URL)
    }
}


// Insert image via a URL

function CreateImage(URL) {
    if ((URL == null) || (URL == "")) {
        URL = prompt(EpozLang["EnterImageURL"], "");
    }
    if ((URL != null) && (URL != "")) {
        EpozElement.contentWindow.focus()
        EpozElement.contentWindow.document.execCommand('InsertImage', false, URL);
    }
}


// Creates a simple table

function CreateTable(rows, cols, border, head) {
    rows = parseInt(rows);
    cols = parseInt(cols);

  if ((rows > 0) && (cols > 0)) {
      table = ' <table border="' + border + '">\n';

    for (var i=0; i < rows; i++) {
          table = table + " <tr>\n";
            for (var j=0; j < cols; j++) {
              if(i==0 && head=="1") {
                   table += "  <th>#</th>\n";
              } else {
                 table += "  <td>#</td>\n";
        }
      }
            table += " </tr>\n";
    }
    table += " </table>\n";
    InsertHTML(table);
  }
    EpozElement.contentWindow.focus()
}


// Sets selected formats

function SelectFormat(selectname)
{
    // First one is only a label
    if (selectname.selectedIndex != 0) {
        EpozElement.contentWindow.document.execCommand(selectname.id, false, selectname.options[selectname.selectedIndex].value);
        selectname.selectedIndex = 0;
    }
    EpozElement.contentWindow.focus();
}


// Sets foreground-color

function SetTextColor() {
    EpozColorCommand='forecolor';
    window.open(form_path+'epoz_script_color.html','EpozColor','toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=220,height=220');
}

// Sets background-color

function SetBackColor() {
    EpozColorCommand='backcolor';
    window.open(form_path+'epoz_script_color.html','EpozColor','toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=220,height=220');
}

// Submit color-command to Rich-Text-Controls

function SetColor(color) {

    if (browser.isGecko) {
       EpozElement.contentWindow.document.execCommand('useCSS',false, false);
    }

    EpozElement.contentWindow.document.execCommand(EpozColorCommand, false, color);
    EpozElement.contentWindow.focus();
}

// Switch between Source- and Wysiwyg-View

function SwitchViewMode(source_mode)
{
    var html = GetHTML(!source_mode);

    if (source_mode) {
        EpozTextArea.value=html;
        document.getElementById("EpozToolbar").style.display="none";
        EpozTextArea.style.display="inline";
    } else {
        html = html.replace('<script ', '<epoz:script style="display: none" ')
        html = html.replace('</script>', '</epoz:script>')

        EpozElement.contentWindow.document.body.innerHTML = html;
        document.getElementById("EpozToolbar").style.display="inline";
        EpozTextArea.style.display="none";

        if (browser.isGecko) {
            EpozElement.contentDocument.designMode = "on";
        }
    }
}

// Keyboard-Handler for Mozilla (supports same shortcuts as IE)

function HandleKeyboardEvent(event)
{
    if (event.ctrlKey) {
        var key = String.fromCharCode(event.charCode).toLowerCase();
        switch (key) {
            case 'b': FormatText('bold',''); event.preventDefault(); break;
            case 'i': FormatText('italic',''); event.preventDefault(); break;
            case 'u': FormatText('underline',''); event.preventDefault(); break;
            case 'k': CreateLink(); event.preventDefault(); break;
        };
    }
}



// This script allows to use several Epoz WYSIWYG fields.
// Copyright (C) 2005 Benoit PIN <mailto:pin@cri.ensmp.fr>

var IFramePrefix = "Iframe_";
var IFramePrefixLength = IFramePrefix.length;
var DocPrefix = "doc_";
var DocPrefixLength = DocPrefix.length;
var CheckBoxPrefix = "CB_";
var CheckBoxPrefixLength = CheckBoxPrefix.length;
var ToolBarPrefix = "ToolBar_";
var ToolBarPrefixLength = ToolBarPrefix.length;


function redirectEpoz(iframe) {
    if(EpozElement) {
        if (EpozElement == iframe) {
            return;
        }
        changeBorderStyle(EpozElement, "dashed");
        unwrapEpozVariables();
    }

    // update Epoz variables
    wrapEpozVariables(iframe);

    //cosmetic
    changeBorderStyle(EpozElement, "solid");
    EpozElement.contentWindow.focus();
}


function wrapEpozVariables(iframe) {
    fieldId = iframe.contentWindow.document.id.slice(DocPrefixLength);

    iframe.id = Epoz ;
    EpozElement=iframe;
    EpozTextArea = document.getElementById(fieldId);
    toolBar = document.getElementById(ToolBarPrefix + fieldId);
    toolBar.id = "EpozToolbar";
    checkBox = document.getElementById(CheckBoxPrefix + fieldId);
    checkBox.id = "EpozViewMode";
}


function unwrapEpozVariables() {
    if (!EpozElement) {
        // no redirection happens yet.
        return;
    }

    fieldId = EpozElement.contentWindow.document.id.slice(DocPrefixLength);

    EpozElement.id = IFramePrefix + fieldId;
    toolBar = document.getElementById("EpozToolbar");
    toolBar.id = ToolBarPrefix + fieldId;
    checkBox = document.getElementById("EpozViewMode");
    checkBox.id = CheckBoxPrefix + fieldId;
}



// Initialization functions

if (!formDatas) {
    var formDatas = new Array();
}

function InitIframe(name, data, path, toolbox, style, button, css, customcss, charset, pageurl) {
    form_name = name;
    form_data = data;
    form_path = path;
    form_toolbox = toolbox;
    form_area_style = style;
    form_button_style = button;
    form_css = css;
    form_customcss = customcss;
    form_charset = charset;
    form_pageurl = pageurl;

    var richText;

    if (browser.isIE55 || browser.isIE6up) {
        // Mac-IE doesn't support RichText-Edit at the moment
        if (browser.isMac) {
            CreateTextarea();
            richText = false;
        } else {
            CreateEpoz();
            richText = true;
        }
    }
    else if (browser.isGecko) {
        //check to see if midas is enabled
        try {
            // Just a few cleanups for Mozilla

            form_data = form_data.replace(/<strong>/ig,'<b>');
            form_data = form_data.replace(/<strong(\s[^>]*)>/ig,'<b$1>');
            form_data = form_data.replace(/<\/strong>/ig,'</b>');

            form_data = form_data.replace(/<em>/ig,'<i>');
            form_data = form_data.replace(/<em(\s[^>]*)>/ig,'<i$1>');
            form_data = form_data.replace(/<\/em>/ig,'</i>');

            CreateEpoz();
            richText = true;
        } catch (e) {
          CreateTextarea();
          richText = false;
        }
    }
    else {
        CreateTextarea();
        richText = false;
    }

    if (richText) {
        // change iframe id
        formDatas[name] = form_data;
        var iframe = document.getElementById(Epoz);
        iframe.id = IFramePrefix + name;

        // change EpozToolbar id
        var toolBar = document.getElementById("EpozToolbar");
        toolBar.id = ToolBarPrefix + name;

        // Retrieve the switch HTML mode checkbox and change id and onclick function.
        nodes = iframe.parentNode.nextSibling.nextSibling.childNodes;
        var i;
        for (i=0 ; i<nodes.length ; i++ ) {
            if (nodes[i].nodeType == 1 && nodes[i].nodeName == 'INPUT')
                break;
        }
        var checkbox = nodes[i];
        checkbox.id = CheckBoxPrefix + name;

        changeBorderStyle(iframe, "dashed");
    }
}



function HandleEpozRedirect() {
    if (browser.isIE55 || browser.isIE6up) {
        iframe = event.srcElement;
    }
    else if (browser.isGecko) {
        iframe = this;
    }
    redirectEpoz(iframe);
}

function redirectAndSwitchViewMode(checkbox) {
    if (checkbox.id != "EpozViewMode") {    // Otherwise, EpozElement already targets the good field.
        var iframe = document.getElementById(IFramePrefix + checkbox.id.slice(CheckBoxPrefixLength));
        redirectEpoz(iframe);
    }
    SwitchViewMode(checkbox.checked);
}


function changeBorderStyle(ob, borderStyle) {
    s = ob.style;
    s.borderBottomStyle = borderStyle;
    s.borderLeftStyle = borderStyle;
    s.borderRightStyle = borderStyle;
    s.borderTopStyle = borderStyle;
}


function SyncEpoz() {
    if (document.getElementsByTagName) {
        var iframes = document.getElementsByTagName("IFRAME");
    }
    else if (document.all) {
        var iframes = document.all.tags("IFRAME");
    }

    for (var i=0;i<iframes.length;i++) {

        unwrapEpozVariables();
        wrapEpozVariables(iframes[i]);

        var html = GetHTML();

        // strip trailing whitespace
        html = (html.replace(/^\s*/,'')).replace(/\s*$/,'');

        // remove single br left by Firefox / Mozilla
        if (html=="<br />" || html=="<br>" || html=="<p></p>") {
            html = "";
        }
        form_name = EpozElement.contentWindow.document.id.slice(DocPrefixLength);
        document.getElementById(form_name).value = html;
    }

}

function EnableDesignMode(iframeId) {
    iframe = document.getElementById(iframeId);
    try {
        iframe.contentDocument.designMode = "on";
        iframe.contentWindow.document.addEventListener("keypress", HandleKeyboardEvent, true);
    } catch (e) {
        scriptExpr = 'EnableDesignMode("' + iframeId + '");';
        setTimeout(scriptExpr, 10);
    }
}



//utils

function retrieveForm(baseOb){
    var pn = baseOb.parentNode;

    while (pn != document) {
        if (pn.nodeName == 'FORM') {
            break;
        } else {
            pn = pn.parentNode;
        }
    }
    return pn;
}


function addListener(ob, eventName, functionReference){
    if (browser.isIE55 || browser.isIE6up) {
        eventName = "on" + eventName;
        ob.attachEvent(eventName, functionReference);
    }
    else if (browser.isGecko) {
        ob.addEventListener(eventName, functionReference, false);
    }

}
