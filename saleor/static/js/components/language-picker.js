$('.language-pick').on('click', (e) => {
  const $target = $(e.currentTarget);
  const $langCode = $target.attr('js-lang');
  const $input = $(`<input name="language" type="hidden" value="${$langCode}">`);
  $('#language-picker').append($input);
  $('#language-picker').submit();
});
