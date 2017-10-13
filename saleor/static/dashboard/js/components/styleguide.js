export default $(document).ready((e) => {
  let styleGuideMenu = $('.styleguide__menu');

  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      styleGuideMenu.addClass('fixed');
    } else {
      styleGuideMenu.removeClass('fixed');
    }
  });
});
