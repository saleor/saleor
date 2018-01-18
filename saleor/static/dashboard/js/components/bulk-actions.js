function moveSelectAllCheckbox(bulk, selectAllState) {
  const $selectAll = $('#select-all-products').parent()[0].innerHTML;
  const $headerContainer = $('thead .bulk-checkbox');
  const $actionBarContainer = $('.data-table-bulk-actions__select-all');
  if (bulk) {
    $headerContainer.html('');
    $actionBarContainer[0].innerHTML = $selectAll;
  } else {
    $actionBarContainer.html('');
    $headerContainer[0].innerHTML = $selectAll;
  }
  $actionBarContainer.find('#select-all-products').prop('checked', selectAllState);
  $('.select-all').on('change', onSelectAll);
}

function updateSelectedItemsText (selectAllState) {
  if ([true, false].indexOf(selectAllState) === -1) {
    selectAllState = false;
  }
  const count = $('.select-item:checked').length - $('#select-all-products:checked').length;
  const $counterTextNode = $('.data-table-bulk-actions__selected-items');
  const $header = $('.data-table-bulk-actions');
  const counterText = ngettext('item selected', 'items selected', count);

  if (!count) {
    $header.addClass('single').removeClass('bulk');
    moveSelectAllCheckbox(false, selectAllState);
  } else {
    $counterTextNode.html(`${count} ${counterText}`);
    $header.addClass('bulk').removeClass('single');
    moveSelectAllCheckbox(true, selectAllState);
  }
}

function onSelectAll (e) {
  const $target = $(e.currentTarget);
  const $targetForm = $target.parents('form');
  const $items = $targetForm.find('.switch-actions');
  $items.prop('checked', $target[0].checked);
  console.log($target[0].checked);
  $target.off('change');
  updateSelectedItemsText($target[0].checked);
}

function onSubmit (e) {
  e.preventDefault();
  const a = $(e.currentTarget);
  $('#bulk-action').val(a.attr('data-action'));
  $('#bulk-actions-form').submit();
}

// -----

updateSelectedItemsText();
$('.select-all').on('click', onSelectAll);
$('.select-item').on('change', updateSelectedItemsText);
$('.data-table-bulk-actions__action-choice a').on('click', onSubmit);
$('.data-table-bulk-actions__dropdown-container .dropdown-content a').on('click', onSubmit);
