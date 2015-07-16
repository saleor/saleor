$(document).ready(function() {
  initSelects();
  $('.button-collapse').sideNav();
  $('.modal-trigger').leanModal();

  var $tabs = $('ul.tabs');
  if ($tabs.length) {
    $tabs.find('.tab').on('click', function (e) {
      window.history.pushState(null, null, e.target.hash);
      var tabSelector = $(this).find('a').attr('href');
      $('.btn-fab').addClass('btn-fab-hidden');
      $(tabSelector + '-btn').removeClass('btn-fab-hidden');
    });

    $tabs.find('a.active').parent().click();
  }

  var $breadcrumbs = $('.breadcrumbs--ellipsed');
  if ($breadcrumbs && !$('.hide-on-large-only').is(':visible')) {
    var $breadcrumbsItems = $('.breadcrumbs--ellipsed-item');
    var breadcrumbsItemWidth = ($breadcrumbs.width() - $breadcrumbs.find('li:first').width()) / $breadcrumbsItems.length;
    $breadcrumbsItems.css('max-width', breadcrumbsItemWidth).dotdotdot({'height': 50});
  }

  $('.modal-trigger-custom').on('click', function (e) {
    var that = this;
    $.ajax({
      url: $(this).data('href'),
      method: 'get',
      success: function (response) {
        var $modal = $($(that).attr('href'));
        $modal.html(response);
        initSelects();
        $modal.openModal();
      }
    });

    e.preventDefault();
  });

  $(document).on('submit', '.form-async', function(e) {
    var that = this;
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
        location.reload();
      }
    });
    e.preventDefault();
  }).on('click', '.modal-close', function() {
    $('.modal').closeModal();
  });
});
Dropzone.options.productImageForm = {
  paramName: "image",
  maxFilesize: 20,
  previewsContainer: ".product-gallery",
  thumbnailWidth: 400,
  thumbnailHeight: 250,
  previewTemplate: $("#template").html(),
  clickable: false,
  init: function() {
    var $dropzoneGhost = $('.dropzone-ghost');
    var $gallery = $('.product-gallery');

    this.on('complete', function() {
      $dropzoneGhost.remove().appendTo($gallery);
    }).on('success', function(e, response) {
      console.log(e, response);
      $(e.previewElement).find('.product-gallery-item-desc').html(e.name);
      $(e.previewElement).attr('data-id', response.id);
      var editLinkHref = $(e.previewElement).find('.card-action-edit').attr('href');
      editLinkHref = editLinkHref.split('/');
      editLinkHref[editLinkHref.length - 2] = response.id;
      $(e.previewElement).find('.card-action-edit').attr('href', editLinkHref.join('/'));
      $(e.previewElement).find('.card-action-edit').show();
      var deleteLinkHref = $(e.previewElement).find('.card-action-delete').attr('href');
      deleteLinkHref = deleteLinkHref.split('/');
      deleteLinkHref[deleteLinkHref.length - 3] = response.id;
      $(e.previewElement).find('.card-action-delete').attr('href', deleteLinkHref.join('/'));
      $(e.previewElement).find('.card-action-delete').show();
    });
  }
};
var el = document.getElementById('product-gallery');
if (el) {
  var sortable = Sortable.create(el, {
    handle: '.card-image',
    onUpdate: function () {
      $.ajax({
        dataType: 'json',
        contentType: "application/json",
        data: JSON.stringify({
          'order': (function () {
            var postData = [];
            $(el).find('.product-gallery-item[data-id]').each(function (i) {
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
  var $items = $(this).parents('form').find('.switch-actions');
  if (this.checked) {
    $items.prop('checked', true);
  } else {
    $items.prop('checked', false);
  }
});
$('.switch-actions').on('change', function() {
  var $btnChecked = $(this).parents('form').find('.btn-show-when-checked');
  var $btnUnchecked = $(this).parents('form').find('.btn-show-when-unchecked');
  if($(this).parents('form').find('.switch-actions:checked').length) {
    $btnChecked.show();
    $btnUnchecked.hide();
  } else {
    $btnUnchecked.show();
    $btnChecked.hide();
  }
});
$('.datepicker').pickadate({
  format: 'd mmmm yyyy',
  formatSubmit: 'yyyy/mm/dd',
  selectYears: 15,
  selectMonths: true
});
function initSelects() {
  $('select:not(.browser-default):not([multiple])').material_select();
  $('select[multiple]').addClass('browser-default').select2();
}
