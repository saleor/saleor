function updateHeader () {
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

$(document).ready((e) => {
  updateHeader();
  $('.select-all').on('change', function () {
    let $items = $(this).parents('form').find('.switch-actions');
    if (this.checked) {
      $items.prop('checked', true);
    } else {
      $items.prop('checked', false);
    }
    updateHeader();
  });
  $('.select-item').on('change', updateHeader);
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
  $('.bulk-actions a').on('click', (e) => {
    const a = $(e.currentTarget);
    $('#bulk-action').val(a.attr('data-action'));
    $('#bulk-actions-form').submit();
  });
});
