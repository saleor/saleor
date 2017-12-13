$(document).ready(function () {
  $('#dashboard-screens').carousel();
  $.ajax({
    url: 'https://api.github.com/repos/mirumee/saleor',
    contentType: 'application/json',
    success: function(res) {
      $('#gh-stars').text(res.stargazers_count);
    },
    error: function(res) {
      $('#gh-stars').text('error')
    }
  })
});
