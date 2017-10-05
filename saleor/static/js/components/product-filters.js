export default $(document).ready((e) => {
  $('.toggle-filter').each(function () {
    let icon = $(this).find('.collapse-filters-icon');
    let ele = $(this).find('.filter-form-field');

    let filterArrowDown = $('.product-filters__attributes').data('icon-down');
    let filterArrowUp = $('.product-filters__attributes').data('icon-up');

    ele.attr('aria-expanded', '');

    $(this).find('.filter-label').on('click', () => {
      if (ele.attr('aria-expanded') !== undefined) {
        ele.removeAttr('aria-expanded').find('input[type="checkbox"], input[type="number"]').each((i, el) => {
          if (!el.checked) {
            $(el.parentNode.parentNode).addClass('d-none');
          }
        });
        icon.find('img').attr('src', filterArrowDown);
      } else {
        ele.attr('aria-expanded', '').find('input[type="checkbox"], input[type="number"]').each((i, el) => {
          $(el.parentNode.parentNode).removeClass('d-none');
        });
        icon.find('img').attr('src', filterArrowUp);
      }
    });
  });
});
