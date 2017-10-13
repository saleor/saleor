export default $(document).ready((e) => {
  let navbarHeight = $('.navbar').outerHeight(true);
  let footerHeight = $('.footer').outerHeight(true);
  let windowHeight = $(window).height();
  $('.maincontent').css('min-height', windowHeight - navbarHeight - footerHeight);
});
