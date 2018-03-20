import Sortable from 'sortablejs';

const menuItems = document.getElementById('menu-items');

if (menuItems) {
  Sortable.create(menuItems, {
    handle: '.sortable__drag-area',
    animation: 150,
    onUpdate: () => {
      const orderedMenuItems = $(menuItems)
        .find('.menu-item[data-id]')
        .map((index, item) => item.dataset.id)
        .toArray();

      // TODO: Get rid of ajax() in favour of fetch()
      $.ajax({
        method: 'POST',
        url: $(menuItems).data('post-url'),
        data: {ordered_menu_items: orderedMenuItems},
        traditional: true,
        headers: {
          'X-CSRFToken': $.cookie('csrftoken')
        }
      });
    }
  });
}
