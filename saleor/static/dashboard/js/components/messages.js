const dataElement = $('#messages-container');
const data = dataElement.data('messages');
const $messages = $('.message');
const offset = 100;
const firstMessageOffset = 250;

// -----

if (data) {
  Object.keys(data).forEach((key) => {
    Materialize.toast(data[key], 5000);
  });
}

setTimeout(() => {
  let timeout = 0;
  $messages.each((index, msg) => {
    setTimeout(() => {
      msg.removeClass('toast--hidden');
    }, timeout + offset);
    timeout += 3000;
    setTimeout(() => {
      msg.addClass('toast--hidden');
    }, timeout - offset);
  });
}, firstMessageOffset);
