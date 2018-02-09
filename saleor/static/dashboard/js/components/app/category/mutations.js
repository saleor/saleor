import gql from 'graphql-tag';

const categoryDelete = gql`
  mutation CategoryDelete($pk: Int!) {
    categoryDelete(pk: $pk) {
      errors
    }
  }
`;
const categoryCreate = gql`
  mutation categoryCreateMutation($name: String!, $description: String!, $parent: Int!) {
    categoryCreate(input: {name: $name, description: $description, parent: $parent}) {
      errors
      category {
        id
        pk
        name
        description
        parent {
          pk
        }
      }
    }
  }
`;
const categoryUpdate = gql`
  mutation categoryUpdateMutation($pk: Int!, $name: String!, $description: String!, $parent: Int!) {
    categoryUpdate(pk: $pk, input: {name: $name, description: $description, parent: $parent}) {
      errors
      category {
        id
        pk
        name
        description
        parent {
          pk
        }
      }
    }
  }
`;

export {
  categoryCreate,
  categoryDelete,
  categoryUpdate
};
