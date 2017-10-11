export default $(document).ready((e) => {
  $('.filters-menu').on('click', (e) => {
    const menuContainer = $('.filters-menu__body');
    if (menuContainer.hasClass('d-none')) {
      menuContainer.removeClass('d-none');
    } else {
      menuContainer.addClass('d-none');
    }
  });
});
