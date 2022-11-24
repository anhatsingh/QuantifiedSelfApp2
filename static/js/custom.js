window.onload = function(){
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  });
}

window.setTimeout(function() {
  $(".autofade").fadeTo(500, 0).slideUp(500, function(){
      $(this).remove(); 
  });
}, 4000);

toastr.options.closeButton = true
toastr.options.progressBar = true

