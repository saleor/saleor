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
