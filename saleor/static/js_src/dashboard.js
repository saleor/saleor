$('.button-collapse').sideNav();
$('select:not(.browser-default)').material_select();
$('.modal-trigger').leanModal();
$('ul.tabs').find('.tab').on('click', function(e) {
  window.history.pushState(null, null, e.target.hash);
});
var el = document.getElementById('product-gallery');
var sortable = Sortable.create(el, {
  onUpdate: function(e) {}
});
