$('.button-collapse').sideNav();
$('select:not(.browser-default)').material_select();
$('.modal-trigger').leanModal();
$('ul.tabs').find('.tab').on('click', function(e) {
  window.history.pushState(null, null, e.target.hash);
});
var el = document.getElementById('product-gallery');
var sortable = Sortable.create(el, {
  onUpdate: function() {
    $.ajax({
      dataType: 'json',
      data: {
        'data': (function () {
          var postData = [];
          $(el).find('.product-gallery-item').each(function (i) {
            postData.push({
              pk: $(this).data('id'),
              order: i
            });
          });
          return JSON.stringify(postData);
        })()
      },
      headers: {
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
      },
      method: 'post',
      url: $(el).data('post-url')
    });
  }
});
