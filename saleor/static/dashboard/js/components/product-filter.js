import {screenSizes} from "./misc";

let prevWindowWidth = null;
let initialized = false;

const moveFilters = () => {
  if(prevWindowWidth !== window.innerWidth) {
    const $collapsibleCard = $('.collapse');
    prevWindowWidth = window.innerWidth;
    if(window.innerWidth < screenSizes.md) {
      $('#product-list').before($('#product-filters'));
      if(!initialized) {
        $collapsibleCard.addClass('collapsed');
        initialized = true;
      }
    } else {
      $('#product-list').after($('#product-filters'));
      $collapsibleCard.removeClass('collapsed');
    }
  }
};

export default $(document).ready(() => {
  if($('.body-products-list').length) {
    moveFilters();
    $(window).on('resize', moveFilters);
  }

  $('.collapse-activate').on('click', (e) => {
    const $collapsibleCard = $('.collapse');
    if($collapsibleCard.hasClass('collapsed')) {
      $collapsibleCard.removeClass('collapsed');
    } else {
      $collapsibleCard.addClass('collapsed');
    }
  })
});
