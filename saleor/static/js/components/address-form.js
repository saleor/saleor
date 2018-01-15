export default $(document).ready((e) => {
  $(function () {
    const $i18nAddresses = $('.i18n-address');
    $i18nAddresses.each(function () {
      const $form = $(this).closest('form');
      const $countryField = $form.find('select[name=country]');
      const $previewField = $form.find('input.preview');
      $countryField.on('change', () => {
        $previewField.val('on');
        $form.submit();
      });
      const $countryAreaList = $form.find('#country_area_list');
      if ($countryAreaList) {
        const $countryAreaField = $form.find('input[name=country_area]');
        const countryAreaOptions = $countryAreaList.find('option').toArray().reduce((options, option) => {
          option = $(option);
          let value = option.val();
          let text = option.text();
          options.push(value);
          if (option !== text) {
            options.push(text);
          }
          return options;
        }, []);
        let countryAreaTimeout = null;
        $countryAreaField.on('change', () => {
          clearTimeout(countryAreaTimeout);
          countryAreaTimeout = setTimeout(() => {
            let lowerCaseValue = $countryAreaField.val().toLowerCase();
            if (lowerCaseValue) {
              let value = countryAreaOptions.find(val => val.toLowerCase() === lowerCaseValue);
              if (value) {
                $countryAreaField.val(value);
              } else {
                let value = countryAreaOptions.find(val => val.toLowerCase().startsWith(lowerCaseValue));
                if (value) {
                  $countryAreaField.val(value);
                } else {
                  let value = countryAreaOptions.find(val => val.toLowerCase().includes(lowerCaseValue));
                  if (value) {
                    $countryAreaField.val(value);
                  }
                }
              }
            }
          }, 500);
        });
        $countryAreaField.trigger('change');
      };
    });
  });

  let $deleteAdressIcons = $('.icons');
  let $deleteAdressIcon = $('.delete-icon');
  let $deleteAddress = $('.address-delete');

  $deleteAdressIcon.on('click', (e) => {
    if ($deleteAddress.hasClass('none')) {
      $deleteAddress.removeClass('none');
      $deleteAdressIcons.addClass('none');
    } else {
      $deleteAddress.addClass('none');
    }
  });

  $deleteAddress.find('.cancel').on('click', (e) => {
    $deleteAddress.addClass('none');
    $deleteAdressIcons.removeClass('none');
  });

  // New address dropdown

  let $addressShow = $('.address_show label');
  let $addressHide = $('.address_hide label');
  let $addressForm = $('.checkout__new-address');
  let $initialValue = $('#address_new_address').prop('checked');
  $addressShow.click((e) => {
    $addressForm.slideDown('slow');
  });
  $addressHide.click((e) => {
    $addressForm.slideUp('slow');
  });
  if ($initialValue) {
    $addressForm.slideDown(0);
  } else {
    $addressForm.slideUp(0);
  }
});
