import Sortable from 'sortablejs';

const sortableContainers = $('.sortable-items-container');
const sortableDataKey = 'post-parameter';

/**
 * Example usage:
 *
 * <ul class="sortable-items-container"
 *     data-post-parameter="sorted_items"
 *     data-post-url="/ajax/sort"
 * >
 *   <li class="sortable-item" data-id="1">item 1</li>
 *   <li class="sortable-item" data-id="2">item 2</li>
 *   <li class="sortable-item" data-id="3">item 3</li>
 * </ul>
 *
 */
sortableContainers.each(function (i, element) {
  // get the key to send when sending Ajax requests
  const postParameterKey = (
    $(element).data(sortableDataKey) ||
    console.warn(sortableDataKey, 'data attribute is undefined or empty for', element)
  );

  Sortable.create(element, {
    handle: '.sortable__drag-area',
    animation: 150,
    onUpdate: () => {
      const orderedItems = $(element)
        .find('.sortable-item[data-id]')
        .map((index, item) => item.dataset.id)
        .toArray();

      const data = {};
      data[postParameterKey] = orderedItems;

      // TODO: Get rid of ajax() in favour of fetch()
      $.ajax({
        method: 'POST',
        url: $(element).data('post-url'),
        data: data,
        traditional: true,
        headers: {
          'X-CSRFToken': $.cookie('csrftoken')
        }
      });
    }
  });
});
