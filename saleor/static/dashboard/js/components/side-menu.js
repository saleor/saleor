import { onScroll } from './utils';

function toggleMenu(e) {
  e.preventDefault();
  $('body').toggleClass('nav-toggled');
}

export const init = $(() => {
  const $mainNavTop = $('.side-nav');
  const $toggleMenu = $('#toggle-menu');

  $toggleMenu.click(toggleMenu);
  if ($mainNavTop.length > 0) {
    const mainNavTop = $mainNavTop.offset().top;
    onScroll(() => {
      $('body').toggleClass(
        'sticky-nav',
        Math.floor($(window).scrollTop()) > Math.ceil(mainNavTop),
      );
    });
  }
});

export {
  init as default,
};
