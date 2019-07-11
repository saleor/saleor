import gql from "graphql-tag";

export const getProductsQuery = gql`
  query GetProducts($cursor: String, $perPage: Int) {
    products(after: $cursor, first: $perPage){
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;

export const getCategoriesQuery = gql`
  query GetCategories($cursor: String, $perPage: Int) {
    categories(after: $cursor, first: $perPage){
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;

export const getCollectionsQuery = gql`
  query GetCollections($cursor: String, $perPage: Int) {
    collections(after: $cursor, first: $perPage){
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;
