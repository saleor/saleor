import Dropzone from 'dropzone';
import Sortable from 'sortablejs';

export default $(document).ready((e) => {
  Dropzone.options.productImageForm = {
    paramName: 'image',
    maxFilesize: 20,
    previewsContainer: '.product-gallery',
    thumbnailWidth: 400,
    thumbnailHeight: 400,
    previewTemplate: $('#template').html(),
    clickable: false,
    init: function () {
      this.on('success', function (e, response) {
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
              $(el).find('.product-gallery-item[data-id]').each(function () {
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
});
