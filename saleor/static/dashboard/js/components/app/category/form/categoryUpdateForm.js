import React, { Component, Fragment } from 'react';
import Grid from 'material-ui/Grid';
import PropTypes from 'prop-types';
import { graphql } from 'react-apollo';
import { withRouter } from 'react-router-dom';

import BaseCategoryForm from './base';
import { categoryDetails } from '../queries';
import { categoryUpdate } from '../mutations';

@withRouter
@graphql(categoryUpdate)
@graphql(categoryDetails, { options: props => ({ variables: { id: props.match.params.id } }) })
class CategoryUpdateForm extends Component {
  static propTypes = {
    data: PropTypes.shape({
      category: PropTypes.object,
      loading: PropTypes.bool,
    }),
    history: PropTypes.object,
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
              title={pgettext('Edit category form card title', 'Edit category')}
              name={category.name}
              description={category.description}
              handleConfirm={this.handleConfirm}
              confirmButtonLabel={pgettext('Dashboard update action', 'Update')}
            />
          </Grid>
        </Grid>
      )}
      </Fragment>
    );
  }
}

export default CategoryUpdateForm;
