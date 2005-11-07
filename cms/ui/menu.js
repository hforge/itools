var ns4=document.layers
var ie4=document.all
var ns6=document.getElementById&&!document.all

function Hide(nObjet) {
 if(ie4) { // Internet explorer
   eval(nObjet).style.visibility = 'hidden';
   eval(nObjet).style.width = '0px'; 
 }
 else if(ns4) { // Netscape 4.x
   document.eval(nObjet).visibility = 'hidden'; 
   eval(nObjet).style.width = '0px'; 
    }
 else if(ns6) { // Netscape 6 (mozilla)
   var divns6 = document.getElementsByTagName("div")
   divns6[nObjet].style.visibility = 'hidden'; 
   divns6[nObjet].style.width = '0px'; 
 }
}

function Hide_All() {
for (i=1; i<6; i++){
    id = 'submenu' + i
    Hide(id)
    }
}

function Show(nObjet) {
 // Hide_All()
 if(ie4) { // Internet explorer
   eval(nObjet).style.visibility = 'visible'; 
   eval(nObjet).style.width = '"150px'; 
 }
 else if(ns4) { // Netscape 4.x
   document.eval(nObjet).visibility = 'show'
   eval(nObjet).style.width = '150px'; 
    }
 else if(ns6) { // Netscape 6 (mozilla)
   var divns6 = document.getElementsByTagName("div")
   divns6[nObjet].style.visibility = 'visible'; 
   divns6[nObjet].style.width = '150px'; 
 }
}
