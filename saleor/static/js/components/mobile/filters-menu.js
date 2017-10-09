export default $(document).ready((e) => {
  $('.filters-menu').on('click', (e) => {
    const t = $('.filters-menu__body');
    if (t.hasClass('d-none')) {
      t.removeClass('d-none');
    } else {
      t.addClass('d-none');
    }
  });
});
