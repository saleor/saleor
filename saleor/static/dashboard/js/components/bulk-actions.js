function updateSelectedItemsText () {
  const count = $('.select-item:checked').length - $('#select-all-products:checked').length;
  const $counterTextNode = $('.data-table-header-action-selected-items');
  const $header = $('.data-table-header-alternative');
  const counterText = ngettext('item selected', 'items selected', count);

  if (!count) {
    $header.addClass('single').removeClass('bulk');
  } else {
    $counterTextNode.html(`${count} ${counterText}`);
    $header.addClass('bulk').removeClass('single');
  }
}

function onSwitchActions (e) {
  const $target = $(e.currentTarget);
  const $targetForm = $target.parents('form');
  const $btnChecked = $targetForm.find('.btn-show-when-checked');
  const $btnUnchecked = $targetForm.find('.btn-show-when-unchecked');
  if ($targetForm.find('.switch-actions:checked').length) {
    $btnChecked.show();
    $btnUnchecked.hide();
  } else {
    $btnUnchecked.show();
    $btnChecked.hide();
  }
}

function onSelectAll (e) {
  const $target = $(e.currentTarget);
  const $targetForm = $target.parents('form');
  const $items = $targetForm.find('.switch-actions');
  $items.prop('checked', $target[0].checked);
  updateSelectedItemsText();
}

function onSubmit (e) {
  e.preventDefault();
  const a = $(e.currentTarget);
  $('#bulk-action').val(a.attr('data-action'));
  $('#bulk-actions-form').submit();
}

// -----

updateSelectedItemsText();
$('.select-all').on('change', onSelectAll);
$('.switch-actions').on('change', onSwitchActions);
$('.select-item').on('change', updateSelectedItemsText);
$('.bulk-actions a').on('click', onSubmit);
