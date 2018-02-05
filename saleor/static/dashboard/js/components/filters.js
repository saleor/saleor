import { screenSizes } from './misc';

let prevWindowWidth = null;
let initialized = false;
let $list = null;
const $filters = $('#filters');

const moveFilters = () => {
  if (prevWindowWidth !== window.innerWidth) {
    const $collapsibleCard = $('.collapse');
    prevWindowWidth = window.innerWidth;
    if (window.innerWidth < screenSizes.md) {
      $list.before($filters);
      if (!initialized) {
        $collapsibleCard.addClass('collapsed');
        initialized = true;
      }
    } else {
      $list.after($filters);
      $collapsibleCard.removeClass('collapsed');
    }
  }
};

// -----

$list = $filters.prev();
if ($filters.length) {
  moveFilters();
  $(window).on('resize', moveFilters);
}

$('.collapse-activate').on('click', (e) => {
  const $collapsibleCard = $('.collapse');
  if ($collapsibleCard.hasClass('collapsed')) {
    $collapsibleCard.removeClass('collapsed');
  } else {
    $collapsibleCard.addClass('collapsed');
  }
});
