const $searchIcon = $('.mobile-search-icon');
const $closeSearchIcon = $('.mobile-close-search');
const $searchForm = $('.search-form');

// -----

$searchIcon.on('click', () => $searchForm.removeClass('search-form--hidden'));
$closeSearchIcon.on('click', () => $searchForm.addClass('search-form--hidden'));
