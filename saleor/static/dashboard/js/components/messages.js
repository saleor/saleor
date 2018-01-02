const dataElement = $('#messages-container');
const data = dataElement.data('messages');

// -----

if(data) {
  Object.keys(data).forEach((key) => {
    Materialize.toast(data[key], 5000);
  });
}
