import gql from 'graphql-tag';

const CategoryChildren = gql`
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
const CategoryDetails = gql`
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
  CategoryChildren,
  CategoryDetails
};
