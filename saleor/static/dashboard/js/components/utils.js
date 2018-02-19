import detectPassiveEvents from 'detect-passive-events';
import { parse, stringify } from 'qs';

function onScroll(func) {
  window.addEventListener('scroll', func, detectPassiveEvents.hasSupport ? {
    passive: true
  } : false);
}

function createQueryString(currentQs, newData) {
  const currentData = parse(currentQs.substr(1));
  const data = stringify(Object.assign({}, currentData, newData));
  return `?${data}`;
}

export {
  onScroll,
  createQueryString
};
