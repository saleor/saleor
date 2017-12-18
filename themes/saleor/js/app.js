function hideNoticeBarOnClick (supportsLocalStorage, $noticeBar) {
  $('#notice-bar-close').on('click', function (e) {
    $noticeBar.addClass('hide');
    if (supportsLocalStorage) {
      localStorage.setItem('lastHiddenNotice', $noticeBar.text());
    }
  });
}

$(document).ready(function () {
  // init carousel widget
  $('#dashboard-screens').carousel();

  // init GitHub Stars widget
  $.ajax({
    url: 'https://api.github.com/repos/mirumee/saleor',
    contentType: 'application/json',
    success: function (res) {
      $('#gh-stars').text(res.stargazers_count);
    },
    error: function (res) {
      $('#gh-stars').text('error');
    }
  });

  // init notice bar
  var $noticeBar = $('.notice-bar');
  if (typeof(Storage) !== 'undefined') {
    if ($noticeBar.text() !== localStorage.getItem('lastHiddenNotice')) {
      $noticeBar.removeClass('hide');
      hideNoticeBarOnClick(true, $noticeBar);
    }
  } else {
    hideNoticeBarOnClick(false, $noticeBar);
  }
});
