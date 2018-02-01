import { initializePaymentRequest } from './paymentRequest';

const checkoutBtn = $('#checkout-btn');
checkoutBtn.on('click', async (e) => {
  e.preventDefault();
  if (window.PaymentRequest) {
    initializePaymentRequest();
  } else {
    redirectToDefaultCheckout();
  }
});

function redirectToDefaultCheckout() {
  window.location.href = checkoutBtn.attr('href');
}
