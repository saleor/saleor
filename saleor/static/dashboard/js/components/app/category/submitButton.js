import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import Button from 'material-ui/Button';
import { graphql } from 'react-apollo';
import { updateCategory, addCategory } from './mutations';
import { CategoryChildren, CategoryDetails } from './queries';


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
      query = addCategory;
      break;
    case 'UPDATE':
      query = updateCategory;
      break;
  }
  const refetchQueries = [
    {
      query: CategoryChildren,
      variables: {
        pk: props.pk
      }
    },
  ];
  if (action === 'UPDATE') {
    refetchQueries.push({
      query: CategoryDetails,
      variables: {
        pk: props.pk
      }
    });
  }
  const EnhancedSubmitButton = graphql(query, {
    options: {
      refetchQueries,
    }
  })(SubmitButton);
  return (
    <EnhancedSubmitButton {...props} />
  );
};

export default withRouter(QuerySwitch);
