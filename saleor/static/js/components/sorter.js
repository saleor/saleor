export default $(document).ready((e) => {
  $(document).ready((e) => {
    $('.sort-by button').on('click', (e) => {
      const parent_container = $(e.currentTarget).parent();
      const list = parent_container.find('.sort-list');
      if (list.hasClass('d-none')) {
        list.removeClass('d-none');
        parent_container.find('.click-area').removeClass('d-none');
      } else {
        list.addClass('d-none');
        parent_container.find('.click-area').addClass('d-none');
      }
    });
    $('.sort-by .click-area').on('click', (e) => {
      $('.sort-by .sort-list').addClass('d-none');
      $(e.currentTarget).addClass('d-none');
    });
  });
});
