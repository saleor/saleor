import { onScroll } from './utils';

export default $(document).ready((e) => {
  onScroll(() => $('.styleguide__menu').toggleClass('fixed', $(window).scrollTop() > 100));
});
