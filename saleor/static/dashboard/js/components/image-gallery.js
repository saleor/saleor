import Dropzone from 'dropzone';
import Sortable from 'sortablejs';

export default $(document).ready((e) => {
  Dropzone.options.productImageForm = {
    paramName: 'image_0',
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
        let orderedImages = (function() {
          let postData = [];
          $(el).find('.product-gallery-item[data-id]').each(function() {
            postData.push($(this).data('id'));
          });
          return postData;
        })();

        $.ajax({
          method: 'POST',
          url: $(el).data('post-url'),
          data: {ordered_images: orderedImages},
          traditional: true,
          headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
          }
        });
      }
    });
  }
});
