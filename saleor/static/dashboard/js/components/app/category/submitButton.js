import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import Button from 'material-ui/Button';
import gql from 'graphql-tag';
import { graphql } from 'react-apollo';

const addCategoryQuery = gql`
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
const updateCategoryQuery = gql`
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

class SubmitButton extends Component {
  constructor(props) {
    super(props);
    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    this.props.mutate({
      variables: {
        name: this.props.name,
        description: this.props.description,
        parent: this.props.parent,
        pk: this.props.pk
      }
    })
      .then(({ data }) => {
        const queryName = this.props.action === 'ADD' ? 'categoryCreate' : 'categoryUpdate';
        this.props.history.push(`/categories/${data[queryName].category.pk}/`);
      });
  }

  render() {
    return (
      <Button
        onClick={this.handleClick}
        color="secondary"
        variant="raised"
      >
        {this.props.children}
      </Button>
    );
  }
}

const QuerySwitch = (props) => {
  const { action } = props;
  let query;
  switch (action) {
    case 'ADD':
      query = addCategoryQuery;
      break;
    case 'UPDATE':
      query = updateCategoryQuery;
      break;
  }
  const EnhancedSubmitButton = graphql(query, {
    options: {
      refetchQueries: [
        'CategoryPage',
        'CategoryDetails'
      ]
    }
  })(SubmitButton);
  return (
    <EnhancedSubmitButton {...props} />
  );
};

export default withRouter(QuerySwitch);
