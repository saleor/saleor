import { initSelects } from './selects';

export default $(document).on('submit', '.form-async', function (e) {
  e.preventDefault();
  alert("Be aware admin pirate! Dashboard runs in read only mode!");
}).on('click', '.modal-close', function () {
  $('.modal').modal('close');
});
