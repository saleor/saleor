const checkoutBtn = $('#checkout-btn');
checkoutBtn.on('click', (e) => {
  e.preventDefault();
  if (window.PaymentRequest) {
    console.log("Can use payment-request API");
    initialize();
  } else {
    console.log("No payment-request API");
    redirectToDefaultCheckout();
  }
});

const globalShippingOptions = [
  {
    id: 'economy',
    label: 'Economy Shipping (5-7 Days)',
    amount: {
      currency: 'USD',
      value: '0',
    },
  }, {
    id: 'express',
    label: 'Express Shipping (2-3 Days)',
    amount: {
      currency: 'USD',
      value: '5',
    },
  }, {
    id: 'next-day',
    label: 'Next Day Delivery',
    amount: {
      currency: 'USD',
      value: '12',
    },
  },
];

function initialize() {
  const supportedPaymentMethods = [
    {
      supportedMethods: 'basic-card',
    }
  ];
  const paymentDetails = {
    total: {
      label: 'Total',
      amount:{
        currency: 'USD',
        value: 100
      }
    }
  };
  const options = {
    requestShipping: true,
  };
  
  const request = new PaymentRequest(
    supportedPaymentMethods,
    paymentDetails,
    options
  );

  request.addEventListener('shippingaddresschange', (event) => {
    const request = event.target;
  
    event.updateWith({
      total: {
        label: 'Total',
        amount: {
          currency: 'USD',
          value: 100,
        },
      },
      shippingOptions: globalShippingOptions,
    });
  });

  request.addEventListener('shippingoptionchange', (event) => {
    console.log(request);
    // Step 1: Get the payment request object.
    const prInstance = event.target;
  
    // Step 2: Get the ID of the selected shipping option.
    const selectedId = prInstance.shippingOption;
  
    // Step 3: Mark selected option
    globalShippingOptions.forEach((option) => {
      option.selected = option.id === selectedId;
    });
  
    // TODO: Update total and display items, including pending states.
  
    event.updateWith({
      total: {
        label: 'Total',
        amount: {
          currency: 'USD',
          value: '0',
        },
      },
      shippingOptions: globalShippingOptions,
    });
  });

  request.show()
    .then((paymentResponse) => {
      console.log('Success');
      return paymentResponse.complete('success')
      .then(() => {
        // create order
        // redirect to order details
      });
    })
    .catch((err => {redirectToDefaultCheckout()}));
}

function redirectToDefaultCheckout() {
  window.location.href = checkoutBtn.attr('href');
}
