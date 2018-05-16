function disableSubsequentClicks (e) {
  e.preventDefault();
}

function initLoadAction (e) {
  $('body').css('cursor', 'progress');
  $(e.target).on('click', disableSubsequentClicks);
}

// -----

$('.load-action').on('click', initLoadAction);
