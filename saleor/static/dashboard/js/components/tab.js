export default $(document).ready(function () {
  let $tabs = $('ul.tabs');
  if ($tabs.length) {
    $tabs.find('.tab').on('click', function (e) {
      let tabSelector = $(this).find('a').attr('href');
      $('.btn-fab').addClass('btn-fab-hidden');
      $(tabSelector + '-btn').removeClass('btn-fab-hidden');
    });

    $tabs.find('a.active').parent().click();
  }
  let $messages = $('.message');
  let timeout = 0;
  let offset = 100;
  let firstMessageOffset = 250;
  setTimeout(function () {
    $messages.each(function () {
      let that = this;
      setTimeout(function () {
        $(that).removeClass('toast--hidden');
      }, timeout + offset);
      timeout += 3000;
      setTimeout(function () {
        $(that).addClass('toast--hidden');
      }, timeout - offset);
    });
  }, firstMessageOffset);
});
