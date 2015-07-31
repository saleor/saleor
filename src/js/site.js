$(document).ready(function() {
  'use strict';

  (function() {
    var placeholder = $('.typed');
    var names = placeholder.data('words');

    function animateTeam() {
      placeholder.typed({
        strings: names,
        typeSpeed: 20,
        backDelay: 3000,
        loop: true
      });
    }

    animateTeam();
  })();

  (function() {
    $('a').smoothScroll();
  })();
});
