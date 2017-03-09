import Dropzone from 'dropzone';
import $ from 'jquery';
import 'materialize-css/dist/js/materialize';
import 'select2';
import Sortable from 'sortablejs';

import '../scss/dashboard/dashboard.scss';

var supportsPassive = false;
try {
  var opts = Object.defineProperty({}, 'passive', {
    get: function() {
      supportsPassive = true;
    }
  });
  window.addEventListener('test', null, opts);
} catch (e) {}

function onScroll(func) {
  window.addEventListener('scroll', func, supportsPassive ? {passive: true} : false);
}

function openModal() {
  $('.modal-trigger-custom').on('click', function (e) {
    let that = this;
    $.ajax({
      url: $(this).data('href'),
      method: 'get',
      success: function (response) {
        let $modal = $($(that).attr('href'));
        $modal.html(response);
        initSelects();
        $modal.modal();
      }
    });

    e.preventDefault();
  });
}

$(document).ready(function() {
  let mainNavTop = $('.side-nav').offset().top;
  let $toggleMenu = $('#toggle-menu');
  function toggleMenu(e) {
    $(document.body).toggleClass('nav-toggled');
    e.preventDefault();
  }
  $toggleMenu.click(toggleMenu);
  onScroll(function() {
    $(document.body).toggleClass('sticky-nav', Math.floor($(window).scrollTop()) > Math.ceil(mainNavTop));
  });
  initSelects();
  $('.modal').modal();

  let $tabs = $('ul.tabs');
  if ($tabs.length) {
    $tabs.find('.tab').on('click', function (e) {
      let tabSelector = $(this).find('a').attr('href');
      $('.btn-fab').addClass('btn-fab-hidden');
      $(tabSelector + '-btn').removeClass('btn-fab-hidden');
    });

    $tabs.find('a.active').parent().click();
  }
  openModal();
  let $messages = $('.message');
  let timeout = 0;
  let offset = 100;
  let firstMessageOffset = 250;
  setTimeout(function() {
    $messages.each(function () {
      let that = this;
      setTimeout(function () {
        $(that).removeClass('toast--hidden');
      }, timeout + offset);
      timeout += 3000;
      setTimeout(function () {
        $(that).addClass('toast--hidden');
      }, timeout - offset);
    });
  }, firstMessageOffset);

  $(document).on('submit', '.form-async', function(e) {
    let that = this;
    $.ajax({
      url: $(that).attr('action'),
      method: 'post',
      data: $(that).serialize(),
      complete: function(response) {
        if (response.status === 400) {
          $(that).parent().html(response.responseText);
          initSelects();
        } else {
          $('.modal-close').click();
        }
      },
      success: function(response) {
        if (response.redirectUrl) {
          window.location.href = response.redirectUrl;
        } else {
          location.reload();
        }
      }
    });
    e.preventDefault();
  }).on('click', '.modal-close', function() {
    $('.modal').modal('close');
  });

  function isTablet() {
    return !$('.hide-on-med-only').is(':visible');
  }
});
Dropzone.options.productImageForm = {
  paramName: 'image',
  maxFilesize: 20,
  previewsContainer: '.product-gallery',
  thumbnailWidth: 400,
  thumbnailHeight: 400,
  previewTemplate: $('#template').html(),
  clickable: false,
  init: function() {
    let $dropzoneMessage = $('.dropzone-message');
    let $gallery = $('.product-gallery');

    this.on('success', function(e, response) {
      $(e.previewElement).find('.product-gallery-item-desc').html(response.image);
      $(e.previewElement).attr('data-id', response.id);
      let editLinkHref = $(e.previewElement).find('.card-action-edit').attr('href');
      editLinkHref = editLinkHref.split('/');
      editLinkHref[editLinkHref.length - 2] = response.id;
      $(e.previewElement).find('.card-action-edit').attr('href', editLinkHref.join('/'));
      $(e.previewElement).find('.card-action-edit').show();
      let deleteLinkHref = $(e.previewElement).find('.card-action-delete').attr('data-href');
      deleteLinkHref = deleteLinkHref.split('/');
      deleteLinkHref[deleteLinkHref.length - 3] = response.id;
      $(e.previewElement).find('.card-action-delete').attr('data-href', deleteLinkHref.join('/'));
      $(e.previewElement).find('.card-action-delete').show();
      $('.no-images').addClass('hide');
      openModal();
    });
  }
};
let el = document.getElementById('product-gallery');
if (el) {
  Sortable.create(el, {
    handle: '.sortable__drag-area',
    onUpdate: function () {
      $.ajax({
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
          'order': (function () {
            let postData = [];
            $(el).find('.product-gallery-item[data-id]').each(function() {
              postData.push($(this).data('id'));
            });
            return postData;
          })()
        }),
        headers: {
          'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        method: 'post',
        url: $(el).data('post-url')
      });
    }
  });
}
$('.select-all').on('change', function() {
  let $items = $(this).parents('form').find('.switch-actions');
  if (this.checked) {
    $items.prop('checked', true);
  } else {
    $items.prop('checked', false);
  }
});
$('.switch-actions').on('change', function() {
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
$('.datepicker').pickadate({
  // The title label to use for the month nav buttons
  labelMonthNext: gettext('Next month'),
  labelMonthPrev: gettext('Previous month'),

  // The title label to use for the dropdown selectors
  labelMonthSelect: gettext('Select a month'),
  labelYearSelect: gettext('Select a year'),

  // Months and weekdays
  monthsFull: [ gettext('January'), gettext('February'), gettext('March'), gettext('April'), gettext('May'), gettext('June'), gettext('July'), gettext('August'), gettext('September'), gettext('October'), gettext('November'), gettext('December') ],
  monthsShort: [ gettext('Jan'), gettext('Feb'), gettext('Mar'), gettext('Apr'), gettext('May'), gettext('Jun'), gettext('Jul'), gettext('Aug'), gettext('Sep'), gettext('Oct'), gettext('Nov'), gettext('Dec') ],
  weekdaysFull: [ gettext('Sunday'), gettext('Monday'), gettext('Tuesday'), gettext('Wednesday'), gettext('Thursday'), gettext('Friday'), gettext('Saturday') ],
  weekdaysShort: [ gettext('Sun'), gettext('Mon'), gettext('Tue'), gettext('Wed'), gettext('Thu'), gettext('Fri'), gettext('Sat') ],

  // Materialize modified
  weekdaysLetter: [ gettext('S'), gettext('M'), gettext('T'), gettext('W'), gettext('T'), gettext('F'), gettext('S') ],
  today: gettext('Today'),
  clear: gettext('Clear'),
  close: gettext('Clear'),
  
  format: 'd mmmm yyyy',
  formatSubmit: 'yyyy-mm-dd',
  selectMonths: true,
  hiddenName: true,
  onClose: function() {
    $(document.activeElement).blur();
  }
});

function initSelects() {
  $('select:not(.browser-default):not([multiple])').material_select();
  $('select[multiple]:not(.browser-default)').select2({width: '100%'});
}
// Clickable rows in dashboard tables
$(document).on('click', 'tr[data-action-go]>td:not(.ignore-link)', function() {
  let target = $(this).parent();
  window.location.href = target.data('action-go');
});

// Coupon dynamic forms
$(document).ready(() => {
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
