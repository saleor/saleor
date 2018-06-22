$('.filters-menu').on('click', (e) => {
  const menuContainer = $('.filters-menu__body');
  if (menuContainer.hasClass('d-none')) {
    menuContainer.removeClass('d-none');
  } else {
    menuContainer.addClass('d-none');
  }
});

$('.filter-section__header').on('click', (event) => {
  const $target = $(event.currentTarget).parent();
  if ($target.attr('aria-expanded') === 'true') {
    $target.attr('aria-expanded', 'false').addClass('filter-section--closed');
  } else {
    $target.attr('aria-expanded', 'true').removeClass('filter-section--closed');
  }
});

$('.filters-toggle').on('click', () => {
  $('.filters-menu__body').toggleClass('d-none');
});
