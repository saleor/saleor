const init = $(() => {
  $('#btn-search').on('click', (e) => {
    e.preventDefault();
    const $target = $(e.currentTarget);
    $('.search').toggleClass('expanded', !$target.hasClass('expanded'));
  });
  $('#btn-search-close').on('click', (e) => {
    const $target = $(e.currentTarget);
    const isExpanded = $target.hasClass('expanded');
    $('.search').toggleClass('expanded', isExpanded);
    $target.toggleClass('active', !isExpanded);
  });
});
export {
  init as default
};
