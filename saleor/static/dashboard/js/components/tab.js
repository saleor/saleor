const $tabs = $('ul.tabs');
if ($tabs.length) {
  $tabs.find('.tab').on('click', (e) => {
    const tabSelector = $(e.currentTarget)
      .find('a')
      .attr('href');
    $('.btn-fab').addClass('btn-fab-hidden');
    $(tabSelector + '-btn').removeClass('btn-fab-hidden');
  });

  $tabs.find('a.active')
    .parent()
    .click();
}
