import gql from 'graphql-tag';

export const CartQuery = gql`
  query Cart {
    cart {
      total {
        currency
        gross
      }
    }
  }
`;

export const ShippingQuery = gql`
  query Shipping($countryCode: String) {
    shipping(countryCode: $countryCode) {
      edges {
        node {
          countryCode
          name
          pk
          price {
            currency
            gross
          }
        }
      }
    }
  }
`;

export const CreateOrderMutation = gql`
  mutation CreateOrder(
    $details: DetailsInput!,
    $methodName: String!,
    $shippingOption: String!,
    $shippingAddress: AddressInput!,
  ) {
    createOrder(
      details: $details,
      methodName: $methodName,
      shippingOption: $shippingOption,
      shippingAddress: $shippingAddress
    ) {
      ok
      redirectUrl
    }
  }
`;
