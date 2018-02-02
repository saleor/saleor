// eslint-disable-next-line no-unused-vars
import Dropzone from 'dropzone';
import Sortable from 'sortablejs';

function createLink (link, index, replacement) {
  const outputLink = link.attr('data-href-template').split('/');
  outputLink[outputLink.length + index] = replacement;
  return outputLink.join('/');
}

const productGallery = document.getElementById('product-gallery');

// -----

$('#product-image-form').dropzone({
  paramName: 'image_0',
  maxFilesize: 20,
  previewsContainer: '.product-gallery',
  thumbnailWidth: 400,
  thumbnailHeight: 400,
  previewTemplate: $('#template').html(),
  method: 'POST',
  clickable: '.dropzone-message',
  init: function () {
    this.on('success', (e, response) => {
      const $previewElement = $(e.previewElement);
      $previewElement.find('.product-gallery-item-desc').html(response.image);
      $previewElement.attr('data-id', response.id);

      const $editLinkElement = $previewElement.find('.card-action-edit');
      const editLinkHref = createLink($editLinkElement, -2, response.id);
      $editLinkElement.attr('href', editLinkHref);

      const $deleteLinkElement = $previewElement.find('.card-action-delete');
      const deleteLinkHref = createLink($deleteLinkElement, -3, response.id);
      $deleteLinkElement.attr('data-href', deleteLinkHref);

      $('.no-images').addClass('hide');
    });
  }
});

if (productGallery) {
  Sortable.create(productGallery, {
    handle: '.sortable__drag-area',
    onUpdate: () => {
      const orderedImages = $(productGallery)
        .find('.product-gallery-item[data-id]')
        .map((index, item) => item.dataset.id)
        .toArray();

      // TODO: Get rid of ajax() in favour of fetch()
      $.ajax({
        method: 'POST',
        url: $(productGallery).data('post-url'),
        data: {ordered_images: orderedImages},
        traditional: true,
        headers: {
          'X-CSRFToken': $.cookie('csrftoken')
        }
      });
    }
  });
}
