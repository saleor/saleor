export default $(document).ready((e) => {
  let $toogleIcon = $('.navbar__brand__menu-toggle');
  let $mobileNav = $('nav');
  let windowWidth = $(window).width();

  if (windowWidth < 767) {
    $mobileNav.append('<ul class="nav navbar-nav navbar__menu__login"></ul>');
    $('.navbar__login a').appendTo('.navbar__menu__login')
      .wrap('<li class="nav-item login-item"></li>')
      .addClass('nav-link');
  }

  $toogleIcon.click((e) => {
    $mobileNav.toggleClass('open');
    e.stopPropagation();
  });
  $(document).click((e) => {
    $mobileNav.removeClass('open');
  });
});
