import client from '../client';
import { CartQuery, ShippingQuery } from './queries';

const getShippingOptions = (shippingQueryResponse, countryCode = '') => {
  let edges = shippingQueryResponse.data.shipping.edges;
  edges = edges.filter(edge => edge.node.countryCode === countryCode || edge.node.countryCode === ''); // ugly check for ANY country
  return edges.map(edge => {
    const shippingOption = edge.node;
    return {
      id: shippingOption.pk,
      label: shippingOption.name,
      amount: {
        currency: shippingOption.price.currency,
        value: shippingOption.price.gross
      }
    };
  });
};

const getPaymentDetails = (cart, shippingOption = undefined) => {
  let totalValue = cart.total.gross;
  if (shippingOption) {
    totalValue += shippingOption.amount.value;
  }
  return {
    total: {
      label: 'Total',
      amount: {
        currency: cart.total.currency,
        value: totalValue
      }
    }
  };
};

export async function initializePaymentRequest() {
  const cartQueryResponse = await client.query({query: CartQuery});
  const shippingQueryResponse = await client.query({query: ShippingQuery});

  const cart = cartQueryResponse.data.cart;
  let shippingOptions;

  const request = new PaymentRequest(
    [
      {
        supportedMethods: 'basic-card'
      }
    ],
    getPaymentDetails(cart),
    {
      requestShipping: true
    }
  );

  request.addEventListener('shippingaddresschange', (event) => {
    shippingOptions = getShippingOptions(shippingQueryResponse, request.shippingAddress.country);
    event.updateWith({
      total: getPaymentDetails(cart).total,
      shippingOptions: shippingOptions
    });
  });

  request.addEventListener('shippingoptionchange', (event) => {
    const selectedId = request.shippingOption;
    let selectedOption;
    shippingOptions.forEach((option) => {
      option.selected = option.id === selectedId;
      if (option.id === selectedId) {
        selectedOption = option;
      };
    });
    event.updateWith({
      total: getPaymentDetails(cart, selectedOption).total,
      shippingOptions: shippingOptions
    });
  });

  try {
    const paymentResponse = await request.show();
    await paymentResponse.complete('success');
    // use paymentResponse to create order and redirect to order details
  } catch (err) {
    console.log(err);
  }
}
