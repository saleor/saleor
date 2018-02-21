import React, { Component } from 'react';
import { graphql } from 'react-apollo';
import { withRouter } from 'react-router-dom';
import Grid from 'material-ui/Grid';

import BaseCategoryForm from './base';
import { categoryCreate } from '../mutations';

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
          parentId: this.props.match.params.id
        }
      })
        .then(({ data }) => this.props.history.push(`/categories/${data.categoryCreate.category.id}/`))
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
            confirmButtonLabel={pgettext('Add category submit action button label', 'Add category')}
          />
        </Grid>
      </Grid>
    );
  }
}

export {
  CategoryCreateForm
};
