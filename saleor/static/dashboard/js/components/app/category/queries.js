import gql from 'graphql-tag';

const categoryChildren = gql`
  query CategoryChildren ($pk: Int) {
    categories(parent: $pk) {
      edges {
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
