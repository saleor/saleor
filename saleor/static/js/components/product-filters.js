export default $(document).ready((e) => {
  $('.toggle-filter').each(function () {
    let icon = $(this).find('.collapse-filters-icon');
    let ele = $(this).find('.filter-form-field');

    let filterArrowDown = $('.product-filters__attributes').data('icon-down');
    let filterArrowUp = $('.product-filters__attributes').data('icon-up');

    $(this).find('.filter-label').on('click', () => {
      if (ele.css('display') == 'block') {
        ele.css('display', 'none');
        icon.find('img').attr('src', filterArrowDown);
      } else {
        ele.css('display', 'block');
        icon.find('img').attr('src', filterArrowUp);
      }
    });
  });
});
