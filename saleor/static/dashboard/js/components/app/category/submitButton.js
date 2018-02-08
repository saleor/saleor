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
      },
    }).then(({ data }) => {
      console.log(data);
      this.props.history.push(`/categories/${data.categoryCreate.category.pk}/`)
    });
  }

  render() {
    return (
      <Button
        onClick={this.handleClick}
        color="secondary"
        variant="raised"
      />
    );
  }

}

const QuerySwitch = (props) => {
  const { action, ...componentProps } = props;
  let query;
  switch (action) {
    case 'ADD':
      query = addCategoryQuery;
      break;
    case 'UPDATE':
      query = updateCategoryQuery;
      break;
  }
  const EnhancedSubmitButton = graphql(query)(SubmitButton);
  return (
    <EnhancedSubmitButton {...componentProps} />
  );
};

export default withRouter(QuerySwitch);
