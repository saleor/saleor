function submit (e) {
  e.preventDefault();
  $(e.currentTarget).parent().submit();
}

function openSearchBar (e) {
  e.preventDefault();
  const $target = $(e.currentTarget);
  $('.search').toggleClass('expanded', !$target.hasClass('expanded'));
}

function closeSearchBar (e) {
  const $target = $(e.currentTarget);
  const isExpanded = $target.hasClass('expanded');
  $('.search').toggleClass('expanded', isExpanded);
  $target.toggleClass('active', !isExpanded);
}

// -----

$('#btn-search').on('click', openSearchBar);
$('#btn-search-close').on('click', closeSearchBar);
$('#btn-search-submit').on('click', submit);
