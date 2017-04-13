import Dropzone from 'dropzone';
import $ from 'jquery';
import 'materialize-css/dist/js/materialize';
import 'select2';
import Sortable from 'sortablejs';
import SVGInjector from 'svg-injector-2';

import '../scss/dashboard.scss';

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

new SVGInjector().inject(document.querySelectorAll('svg[data-src]'));

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

  let styleGuideMenu = $('.styleguide__menu');

  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      styleGuideMenu.addClass("fixed");
    } else {
      styleGuideMenu.removeClass("fixed");
    }
  })

  let mainNavTop = $('.side-nav');
  let $toggleMenu = $('#toggle-menu');
  function toggleMenu(e) {
    $(document.body).toggleClass('nav-toggled');
    e.preventDefault();
  }
  $toggleMenu.click(toggleMenu);
  if (mainNavTop.length > 0) {
    mainNavTop = mainNavTop.offset().top;
    onScroll(function() {
      $(document.body).toggleClass('sticky-nav', Math.floor($(window).scrollTop()) > Math.ceil(mainNavTop));
    });
  }
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
  labelMonthNext: pgettext('Datepicker option', 'Next month'),
  labelMonthPrev: pgettext('Datepicker option', 'Previous month'),

  // The title label to use for the dropdown selectors
  labelMonthSelect: pgettext('Datepicker option', 'Select a month'),
  labelYearSelect: pgettext('Datepicker option', 'Select a year'),

  // Months and weekdays
  monthsFull: [ pgettext('Datepicker month', 'January'), pgettext('Datepicker month', 'February'), pgettext('Datepicker month', 'March'), pgettext('Datepicker month', 'April'), pgettext('Datepicker month', 'May'), pgettext('Datepicker month', 'June'), pgettext('Datepicker month', 'July'), pgettext('Datepicker month', 'August'), pgettext('Datepicker month', 'September'), pgettext('Datepicker month', 'October'), pgettext('Datepicker month', 'November'), pgettext('Datepicker month', 'December') ],
  monthsShort: [ pgettext('Datepicker month shortcut', 'Jan'), pgettext('Datepicker month shortcut', 'Feb'), pgettext('Datepicker month shortcut', 'Mar'), pgettext('Datepicker month shortcut', 'Apr'), pgettext('Datepicker month shortcut', 'May'), pgettext('Datepicker month shortcut', 'Jun'), pgettext('Datepicker month shortcut', 'Jul'), pgettext('Datepicker month shortcut', 'Aug'), pgettext('Datepicker month shortcut', 'Sep'), pgettext('Datepicker month shortcut', 'Oct'), pgettext('Datepicker month shortcut', 'Nov'), pgettext('Datepicker month shortcut', 'Dec') ],
  weekdaysFull: [ pgettext('Datepicker weekday', 'Sunday'), pgettext('Datepicker weekday', 'Monday'), pgettext('Datepicker weekday', 'Tuesday'), pgettext('Datepicker weekday', 'Wednesday'), pgettext('Datepicker weekday', 'Thursday'), pgettext('Datepicker weekday', 'Friday'), pgettext('Datepicker weekday', 'Saturday') ],
  weekdaysShort: [ pgettext('Datepicker weekday shortcut', 'Sun'), pgettext('Datepicker weekday shortcut', 'Mon'), pgettext('Datepicker weekday shortcut', 'Tue'), pgettext('Datepicker weekday shortcut', 'Wed'), pgettext('Datepicker weekday shortcut', 'Thu'), pgettext('Datepicker weekday shortcut', 'Fri'), pgettext('Datepicker weekday shortcut', 'Sat') ],

  // Materialize modified
  weekdaysLetter: [ pgettext('Sunday shortcut','S'), pgettext('Monday shortcut','M'), pgettext('Tuesday shortcut','T'), pgettext('Wednesday shortcut','W'), pgettext('Thursday shortcut','T'), pgettext('Friday shortcut','F'), pgettext('Saturday shortcut','S') ],
  today: pgettext('Datepicker option', 'Today'),
  clear: pgettext('Datepicker option', 'Clear'),
  close: pgettext('Datepicker option','Close'),
  
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

//Print button
$('.btn-print').click((e) => {
  window.print();
});
