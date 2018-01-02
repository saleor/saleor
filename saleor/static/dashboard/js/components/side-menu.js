import { onScroll } from './utils';

function toggleMenu (e) {
  e.preventDefault();
  $('body').toggleClass('nav-toggled');
}

const $mainNavTop = $('.side-nav');
const $toggleMenu = $('#toggle-menu');

// -----

if ($mainNavTop.length) {
  const mainNavTop = $mainNavTop.offset().top;
  $toggleMenu.on('click', toggleMenu);
  if ($mainNavTop.length > 0) {
    onScroll(() => {
      const stickSideMenu = Math.floor($(window).scrollTop()) > Math.ceil(mainNavTop);
      $('body').toggleClass('sticky-nav', stickSideMenu);
    });
  }
}
