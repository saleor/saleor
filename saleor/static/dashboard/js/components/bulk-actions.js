$(document).ready((e) => {
  $('.select-all').on('change', function () {
    let $items = $(this).parents('form').find('.switch-actions');
    if (this.checked) {
      $items.prop('checked', true);
    } else {
      $items.prop('checked', false);
    }
  });
  $('.switch-actions').on('change', function () {
    let $btnChecked = $(this).parents('form').find('.btn-show-when-checked');
    let $btnUnchecked = $(this).parents('form').find('.btn-show-when-unchecked');
    if ($(this).parents('form').find('.switch-actions:checked').length) {
      $btnChecked.show();
      $btnUnchecked.hide();
    } else {
      $btnUnchecked.show();
      $btnChecked.hide();
    }
  });
});
