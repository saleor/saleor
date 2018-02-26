import React, { Component } from 'react';
import Grid from 'material-ui/Grid';
import PropTypes from 'prop-types';
import { graphql } from 'react-apollo/index';
import { withRouter } from 'react-router-dom';

import BaseCategoryForm from './base';
import { categoryCreate } from '../mutations';

@withRouter
@graphql(categoryCreate)
class CategoryCreateForm extends Component {
  static propTypes = {
    history: PropTypes.history,
    match: PropTypes.object,
    mutate: PropTypes.func,
  };

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

export default CategoryCreateForm;
