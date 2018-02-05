/*
 * Handler for voucher type change event. Manages showing options
 * that are connected to selected voucher type and hiding others.
 */
function onVoucherTypeChange (e) {
  const $target = $(e.currentTarget);
  $('.voucher-form').each((index, form) => {
    const $form = $(form);
    $form.toggleClass('hide', $form.data('type') !== $target.val());
  });
}

/*
 * Handler for discount type change event. Shows additional options
 * if 'percentage' option is selected.
 */
function onDiscountTypeChange (e) {
  const $target = $(e.currentTarget);
  const showOnPercentage = '[name="product-apply_to"], [name="category-apply_to"]';
  const $showOnPercentage = $(showOnPercentage).parents('.input');
  $showOnPercentage.toggleClass('hide', $target.val() === 'percentage');
}

// -----

$('[name="discount_value_type"]')
  .on('change', onDiscountTypeChange)
  .trigger('change');
$('[name="type"]')
  .on('change', onVoucherTypeChange)
  .trigger('change');
