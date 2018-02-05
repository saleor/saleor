import detectPassiveEvents from 'detect-passive-events';

function onScroll(func) {
  window.addEventListener('scroll', func, detectPassiveEvents.hasSupport ? {
    passive: true
  } : false);
}

export {
  onScroll
};
