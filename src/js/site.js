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

  $('.tracked-outbound-link').on('click', function(e) {
    trackOutboundLink($(this).attr('href'));
    e.preventDefault();
  });
});

(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-10159761-12', 'auto');
ga('send', 'pageview');

var trackOutboundLink = function(url) {
   ga('send', 'event', 'outbound', 'click', url, {'hitCallback':
     function () {
       document.location = url;
     }
   });
};
