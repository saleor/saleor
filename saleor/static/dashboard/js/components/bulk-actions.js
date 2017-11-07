function updateCounterSelected () {
  const count = $('.select-item:checked').length;
  const $counterTextNode = $('.data-table-header-action-selected-items');
  let counterText;

  if (count === 1) {
    counterText = pgettext('bulk action select label one', 'item selected');
  } else {
    counterText = pgettext('bulk action select label multiple', 'items selected');
  }

  $counterTextNode.html(count ? `${count} ${counterText}` : counterText);
  if (!count) {
    $counterTextNode.addClass('hide');
  } else {
    $counterTextNode.removeClass('hide');
  }
}

$(document).ready((e) => {
  $('.select-all').on('change', function () {
    let $items = $(this).parents('form').find('.switch-actions');
    if (this.checked) {
      $items.prop('checked', true);
    } else {
      $items.prop('checked', false);
    }
    updateCounterSelected();
  });
  $('.select-item').on('change', function () {
    updateCounterSelected();
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
