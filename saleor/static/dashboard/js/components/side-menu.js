import {onScroll} from './utils';

export default $(document).ready((e) => {
  let mainNavTop = $('.side-nav');
  let $toggleMenu = $('#toggle-menu');

  function toggleMenu(e) {
    $(document.body).toggleClass('nav-toggled');
    e.preventDefault();
  }

  $toggleMenu.click(toggleMenu);
  if (mainNavTop.length > 0) {
    mainNavTop = mainNavTop.offset().top;
    onScroll(function () {
      $(document.body).toggleClass('sticky-nav', Math.floor($(window).scrollTop()) > Math.ceil(mainNavTop));
    });
  }
});
