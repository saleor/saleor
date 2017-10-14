export default $(document).ready(() => {
  let $voucherTypeInput = $('.body-vouchers [name="type"]');
  if ($voucherTypeInput.length) {
    let $discountValueType = $('[name="discount_value_type"]');
    let $voucherForms = $('.voucher-form');
    let $applyToProduct = $('[name="product-apply_to"]').parents('.input');
    let $applyToCategory = $('[name="category-apply_to"]').parents('.input');
    let onChange = () => {
      let discountValueType = $discountValueType.val();
      let type = $voucherTypeInput.val();
      let hide = discountValueType === 'percentage';
      $applyToProduct.toggleClass('hide', hide);
      $applyToCategory.toggleClass('hide', hide);

      $voucherForms.each((index, form) => {
        let $form = $(form);
        let hideForm = $form.data('type') !== type;
        $form.toggleClass('hide', hideForm);
      });
    };

    $discountValueType.on('change', onChange);
    $voucherTypeInput.on('change', onChange);
    $voucherTypeInput.trigger('change');
  }
});
