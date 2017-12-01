import { initSelects } from './utils';

const onAsyncFormSubmit = (e) => {
  e.preventDefault();
  const $target = $(e.currentTarget);
  fetch($target.attr('action'), {
    method: 'POST',
    body: new FormData($target[0]),
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': $.cookie('csrftoken'),
    },
  }).then((res) => {
    let output;
    if (res.status !== 200) {
      output = new Error(res.statusText);
    } else {
      output = res.text();
    }
    return output;
  }).then((data) => {
    if (data.redirectUrl) {
      window.location.href = data.redirectUrl;
    } else {
      window.location.reload();
    }
  }).catch((err) => {
    $target.parent().html(err);
    initSelects();
  });
};

const onModalClose = () => $('.modal').modal('close');

const init = $(document).on('submit', '.form-async', onAsyncFormSubmit)
  .on('click', '.modal-close', onModalClose);

export {
  init as default,
};
