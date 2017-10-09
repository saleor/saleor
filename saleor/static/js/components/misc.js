import SVGInjector from 'svg-injector-2';
import {$removeProductSuccess} from './cart';

export const getAjaxError = (response) => {
  let ajaxError = $.parseJSON(response.responseText).error.quantity;
  return ajaxError;
};
export const csrftoken = $.cookie('csrftoken');

export default $(document).ready((e) => {
  function csrfSafeMethod(method) {
    return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
  }

  if ($.cookie('alert') === 'true') {
    $removeProductSuccess.removeClass('hidden-xs-up');
    $.cookie('alert', 'false', {path: '/cart'});
  }

  new SVGInjector().inject(document.querySelectorAll('svg[data-src]'));

  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      }
    }
  });

  // Open tab from the link

  let hash = window.location.hash;
  $('.nav-tabs a[href="' + hash + '"]').tab('show');
});
