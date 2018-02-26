import React, { Component, Fragment } from 'react';
import { graphql } from 'react-apollo';
import { withRouter } from 'react-router-dom';
import Grid from 'material-ui/Grid';

import BaseCategoryForm from './base';
import { categoryCreate, categoryUpdate } from '../mutations';
import { categoryDetails } from '../queries';

@withRouter
@graphql(categoryCreate)
class CategoryCreateForm extends Component {
  constructor(props) {
    super(props);
    this.handleConfirm = this.handleConfirm.bind(this);
  }

  handleConfirm(formData) {
    return () => {
      this.props.mutate({
        variables: {
          ...formData,
          parentId: this.props.match.params.id,
        },
      })
        .then(({ data }) => this.props.history.push(`/categories/${data.categoryCreate.category.id}/`));
    };
  }

  render() {
    return (
      <Grid container spacing={16}>
        <Grid item xs={12} md={9}>
          <BaseCategoryForm
            title={pgettext('Add category form card title', 'Add category')}
            name=""
            description=""
            handleConfirm={this.handleConfirm}
            confirmButtonLabel={pgettext('Dashboard create action', 'Add')}
          />
        </Grid>
      </Grid>
    );
  }
}

@withRouter
@graphql(categoryUpdate)
@graphql(categoryDetails, { options: props => ({ variables: { id: props.match.params.id } }) })
class CategoryUpdateForm extends Component {
  constructor(props) {
    super(props);
    this.handleConfirm = this.handleConfirm.bind(this);
  }

  handleConfirm(formData) {
    return () => {
      this.props.mutate({
        variables: {
          ...formData,
          id: this.props.match.params.id,
        },
      })
        .then(({ data }) => this.props.history.push(`/categories/${data.categoryUpdate.category.id}/`))
        .catch(error => console.error(error));
    };
  }

  render() {
    const { loading, category } = this.props.data;
    return (
      <Fragment>
        {loading || (
        <Grid container spacing={16}>
          <Grid item xs={12} md={9}>
            <BaseCategoryForm
              title={category.name}
              name={category.name}
              description={category.description}
              handleConfirm={this.handleConfirm}
              confirmButtonLabel={pgettext('Dashboard update action', 'Update ')}
            />
          </Grid>
        </Grid>
      )}
      </Fragment>
    );
  }
}

export {
  CategoryCreateForm,
  CategoryUpdateForm,
};
