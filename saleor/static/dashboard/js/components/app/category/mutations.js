import gql from 'graphql-tag';

const categoryDelete = gql`
  mutation CategoryDelete($pk: Int!) {
    categoryDelete(pk: $pk) {
      errors {
        field
        message
      }
    }
  }
`;
const categoryCreate = gql`
  mutation categoryCreateMutation($name: String!, $description: String!, $parent: Int) {
    categoryCreate(data: {name: $name, description: $description, parent: $parent}) {
      errors {
        field
        message
      }
      category {
        id
        pk
        name
        description
        parent {
          id
          pk
        }
      }
    }
  }
`;
const categoryUpdate = gql`
  mutation categoryUpdateMutation($pk: Int!, $name: String!, $description: String!, $parent: Int) {
    categoryUpdate(pk: $pk, data: {name: $name, description: $description, parent: $parent}) {
      errors {
        field
        message
      }
      category {
        id
        pk
        name
        description
        parent {
          id
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
