import gql from 'graphql-tag';

const categoryChildren = gql`
  query CategoryChildren ($pk: Int, $first: Int, $after: String, $last: Int, $before: String) {
    categories(parent: $pk, first: $first, after: $after, last: $last, before: $before) {
      edges {
        cursor
        node {
          id
          pk
          name
          description
        }
      }
    }
  }
`;
const categoryDetails = gql`
  query CategoryDetails($pk: Int!) {
    category(pk: $pk) {
      id
      pk
      name
      description
      parent {
        pk
      }
    }
  }
`;

export {
  categoryChildren,
  categoryDetails
};
