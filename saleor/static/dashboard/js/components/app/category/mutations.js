import gql from 'graphql-tag';

const deleteCategory = gql`
  mutation CategoryDelete($pk: Int!) {
    categoryDelete(pk: $pk) {
      errors
    }
  }
`;
const addCategory = gql`
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
const updateCategory = gql`
  mutation categoryUpdateMutation($pk: Int!, $name: String!, $description: String!) {
    categoryUpdate(pk: $pk, input: {name: $name, description: $description}) {
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
  addCategory,
  deleteCategory,
  updateCategory
};
