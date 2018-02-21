import gql from 'graphql-tag';

const categoryDelete = gql`
  mutation CategoryDelete($id: ID!) {
    categoryDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
const categoryCreate = gql`
  mutation categoryCreateMutation($name: String!, $description: String, $parentId: ID) {
    categoryCreate(name: $name, description: $description, parentId: $parentId) {
      errors {
        field
        message
      }
      category {
        id
        name
        description
        parent {
          id
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
        name
        description
        parent {
          id
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
