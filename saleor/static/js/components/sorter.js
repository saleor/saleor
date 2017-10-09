export default $(document).ready((e) => {
  $(document).ready((e) => {
    $('.sort-by button').on('click', (e) => {
      const t = $(e.currentTarget).parent();
      const l = t.find('.sort-list');
      if (l.hasClass('d-none')) {
        l.removeClass('d-none');
        t.find('.click-area').removeClass('d-none');
      } else {
        l.addClass('d-none');
        t.find('.click-area').addClass('d-none');
      }
    });
    $('.sort-by .click-area').on('click', (e) => {
      $('.sort-by .sort-list').addClass('d-none');
      $(e.currentTarget).addClass('d-none');
    });
  });
});
