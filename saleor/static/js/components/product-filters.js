export default $(document).ready((e) => {
  $('.filters-menu').on('click', (e) => {
    const menuContainer = $('.filters-menu__body');
    if (menuContainer.hasClass('d-none')) {
      menuContainer.removeClass('d-none');
    } else {
      menuContainer.addClass('d-none');
    }
  });

  $('.toggle-filter').each(function () {
    let icon = $(this).find('.collapse-filters-icon');
    let fields = $(this).find('.filter-form-field');

    let filterArrowDown = $('.product-filters__attributes').data('icon-down');
    let filterArrowUp = $('.product-filters__attributes').data('icon-up');

    fields.attr('aria-expanded', '');

    $(this).find('.filter-label').on('click', () => {
      if (fields.attr('aria-expanded') !== undefined) {
        fields.removeAttr('aria-expanded').find('input[type="checkbox"], input[type="number"]').each((i, field) => {
          if (!field.checked) {
            $(field.parentNode.parentNode).addClass('d-none');
          }
        });
        icon.find('img').attr('src', filterArrowDown);
      } else {
        fields.attr('aria-expanded', '').find('input[type="checkbox"], input[type="number"]').each((i, field) => {
          $(field.parentNode.parentNode).removeClass('d-none');
        });
        icon.find('img').attr('src', filterArrowUp);
      }
    });
  });
});
