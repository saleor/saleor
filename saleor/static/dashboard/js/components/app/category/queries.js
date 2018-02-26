import gql from 'graphql-tag';

const categoryChildren = gql`
  query CategoryChildren ($id: ID!, $first: Int, $after: String, $last: Int, $before: String) {
    category(id: $id) {
      id
      children(first: $first, after: $after, last: $last, before: $before) {
        totalCount
        edges {
          cursor
          node {
            id
            name
            description
          }
        }
      }
    }
  }
`;
const categoryDetails = gql`
  query CategoryDetails($id: ID!) {
    category(id: $id) {
      id
      name
      description
      parent {
        id
      }
      products {
        totalCount
      }
    }
  }
`;
const rootCategoryChildren = gql`
  query RootCategoryChildren($first: Int, $after: String, $last: Int, $before: String) {
    categories(level: 0, first: $first, after: $after, last: $last, before: $before) {
      totalCount
      edges {
        cursor
        node {
          id
          name
          description
        }
      }
    }
  }
`;

export {
  categoryChildren,
  categoryDetails,
  rootCategoryChildren,
};
