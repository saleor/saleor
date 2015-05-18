$(document).ready(function() {
  'use strict';

  var stringSplice = function(orig, index, toRemove, str) {
    return (orig.slice(0, index) + str + orig.slice(index + Math.abs(toRemove)));
  };

  (function() {
    var placeholder = $('.jumbotron .typed');
    var names = placeholder.data("words");

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
});
