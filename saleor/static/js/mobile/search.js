export default $(document).ready((e) => {
  let $searchIcon = $('.mobile-search-icon');
  let $closeSearchIcon = $('.mobile-close-search');
  let $searchForm = $('.search-form');
  $searchIcon.click((e) => {
    $searchForm.animate({left: 0}, {duration: 500});
  });
  $closeSearchIcon.click((e) => {
    $searchForm.animate({left: '-100vw'}, {duration: 500});
  });
});
