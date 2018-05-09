import Sortable from 'sortablejs';

$('.sortable-items').each(function() {
  Sortable.create(this, {
    handle: '.sortable__drag-area',
    animation: 150,
    onUpdate: () => {
      const sortedItems = $(this)
        .find('.sortable-item[data-id]')
        .map((index, item) => item.dataset.id)
        .toArray();
      const data = {};
      data[$(this).data('post-name')] = sortedItems;

      // TODO: Get rid of ajax() in favour of fetch()
      $.ajax({
        method: 'POST',
        url: $(this).data('post-url'),
        data: data,
        traditional: true,
        headers: {
          'X-CSRFToken': $.cookie('csrftoken')
        }
      });
    }
  });
});
