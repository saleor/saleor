/**
 * This function adds .highlight class on checked table rows on page load and select all action.
 * Fixes bug when user checks some items, goes to another page, then goes back in browsing history
 * and some rows are checked but have no .highlight class.
 */
function initCheckedRows () {
  $('.select-item:checked:not(#select-all-items)')
    .each((itemIndex, item) => {
      $(item)
        .parent()
        .parent()
        .addClass('highlight');
    });
  $('.select-item:not(:checked):not(#select-all-items)')
    .each((itemIndex, item) => {
      $(item)
        .parent()
        .parent()
        .removeClass('highlight');
    });
}

function moveSelectAllCheckbox (bulk, selectAllState) {
  const $selectAll = $('#select-all-items')
    .parent()[0].innerHTML;
  const $headerContainer = $('thead .bulk-checkbox');
  const $actionBarContainer = $('.data-table-bulk-actions__select-all');
  if (bulk) {
    $headerContainer.html('');
    $actionBarContainer[0].innerHTML = $selectAll;
  } else {
    $actionBarContainer.html('');
    $headerContainer[0].innerHTML = $selectAll;
  }
  $actionBarContainer.find('#select-all-items')
    .prop('checked', selectAllState);
  $('.select-all')
    .on('change', onSelectAll);
}

function onItemSelect (e) {
  const count = $('.select-item:checked').length - $('#select-all-items:checked').length;
  const maxCount = $('.select-item').length - 1;
  const $target = $(e.currentTarget);
  $target.parent()
    .parent()
    .toggleClass('highlight', $target.checked);
  updateSelectedItemsText(count === maxCount);
}

function onPageInit () {
  if (document.querySelector('#bulk-action')) {
    initCheckedRows();
    updateSelectedItemsText();
    $('.select-all')
      .on('change', onSelectAll);
    $('.select-item')
      .on('change', onItemSelect);
    $('.data-table-bulk-actions__action-choice a')
      .on('click', onSubmit);
    $('.data-table-bulk-actions__dropdown-container .dropdown-content a')
      .on('click', onSubmit);
  }
}

function onSelectAll (e) {
  const $target = $(e.currentTarget);
  const $targetForm = $target.parents('form');
  const $items = $targetForm.find('.select-item:not(.select-all)');
  $items.prop('checked', $target[0].checked);
  initCheckedRows();
  $target.off('change');
  updateSelectedItemsText($target[0].checked);
}

function onSubmit (e) {
  const a = $(e.currentTarget);
  e.preventDefault();
  $('#bulk-action')
    .val(a.attr('data-action'));
  $('#bulk-actions-form')
    .submit();
}

function updateSelectedItemsText (selectAllState) {
  const count = $('.select-item:checked').length - $('#select-all-items:checked').length;
  const $counterTextNode = $('.data-table-bulk-actions__selected-items');
  const $header = $('.data-table-bulk-actions');
  const counterText = ngettext('item selected', 'items selected', count);

  if (count) {
    $counterTextNode.html(`${count} ${counterText}`);
  }
  $header.toggleClass('show', count > 0);
  moveSelectAllCheckbox(count > 0, selectAllState);
}

// -----

onPageInit();
