const $toogleIcon = $('.navbar__brand__menu-toggle');
const $mobileNav = $('nav');
const $searchIcon = $('.mobile-search-icon');
const $closeSearchIcon = $('.mobile-close-search');
const $searchForm = $('.search-form');

const renderNavbar = () => {
  const $desktopLinkBar = $('.navbar__login');
  const $mobileLinkBar = $('.navbar__menu__login');
  const windowWidth = window.innerWidth;
  const $languagePicker = $('.language-picker');

  if (windowWidth < 768) {
    const $desktopLinks = $desktopLinkBar.find('a').not('.dropdown-link');
    if ($desktopLinks.length) {
      $searchForm.addClass('search-form--hidden');
      $mobileNav.append('<ul class="nav navbar-nav navbar__menu__login"></ul>');
      $languagePicker.appendTo('.navbar__menu__login')
        .wrap('<li class="nav-item login-item"></li>')
        .addClass('nav-link');
      $desktopLinks
        .appendTo('.navbar__menu__login')
        .wrap('<li class="nav-item login-item"></li>')
        .addClass('nav-link');
      $desktopLinkBar
        .find('li')
        .remove();
    }
  } else {
    const $mobileLinks = $mobileLinkBar.find('a').not('.dropdown-link');
    if ($mobileLinks.length) {
      $searchForm.removeClass('search-form--hidden');
      $languagePicker.appendTo('.navbar__login ul')
        .wrap('<li></li>')
        .removeClass('nav-link');
      $mobileLinks
        .appendTo('.navbar__login ul')
        .wrap('<li></li>')
        .removeClass('nav-link');
      $mobileLinkBar.remove();
    }
  }
};

// -----

renderNavbar();
$toogleIcon
  .on('click', (e) => {
    $mobileNav.toggleClass('open');
    e.stopPropagation();
  });
$(document)
  .on('click', () => $mobileNav.removeClass('open'));
$(window)
  .on('resize', renderNavbar);
$searchIcon
  .on('click', () => $searchForm.removeClass('search-form--hidden'));
$closeSearchIcon
  .on('click', () => $searchForm.addClass('search-form--hidden'));
