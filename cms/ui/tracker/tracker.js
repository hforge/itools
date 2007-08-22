function reply(id){
  var comment = document.getElementById('comment'+id).innerHTML;
  comment = comment.split(/\r|\n/);
  replytext = ''
  for (var i=0; i < comment.length; i++){
    replytext += "> " + comment[i] + "\n";
  }
  replytext = "(In reply to comment #" + id + ")\n" + replytext + "\n";
  var textarea = document.getElementById('comment')
  textarea.value = replytext
  textarea.focus();
}
