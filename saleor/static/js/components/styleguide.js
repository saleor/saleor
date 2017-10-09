export default $(document).ready(function () {
  let styleGuideMenu = $('.styleguide__nav');
  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      styleGuideMenu.addClass('fixed');
    } else {
      styleGuideMenu.removeClass('fixed');
    }
  });
});
