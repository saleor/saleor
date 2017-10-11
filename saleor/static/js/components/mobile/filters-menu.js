export default $(document).ready((e) => {
  $('.filters-menu').on('click', (e) => {
    const menu_container = $('.filters-menu__body');
    if (menu_container.hasClass('d-none')) {
      menu_container.removeClass('d-none');
    } else {
      menu_container.addClass('d-none');
    }
  });
});
