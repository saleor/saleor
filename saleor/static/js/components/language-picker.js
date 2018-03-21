$('.language-pick').on('click', (e) => {
  const $option = $(e.currentTarget);
  const $langCode = $option.data('lang');
  const $input = $(`<input name="language" type="hidden" value="${$langCode}">`);
  const $languagePickerForm = $('#language-picker');
  $languagePickerForm.append($input);
  $languagePickerForm.submit();
});
