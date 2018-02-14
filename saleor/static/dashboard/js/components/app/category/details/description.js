import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { graphql, compose } from 'react-apollo';
import { CircularProgress } from 'material-ui/Progress';

import { ConfirmRemoval } from '../../../components/modals';
import { DescriptionCard } from '../../../components/cards';
import { categoryDetails as query, categoryChildren } from '../queries';
import { categoryDelete as mutation } from '../mutations';

const categoryDeleteMutation = graphql(mutation, {
  options: (props) => {
    const { data } = props;
    return {
      refetchQueries: [
        {
          query: categoryChildren,
          variables: { pk: (data.category && data.category.parent) ? data.category.parent.pk : '' }
        }
      ]
    };
  }
});
const categoryDetailsQuery = graphql(query, {
  options: (props) => ({
    pk: props.pk
  })
});

@withRouter
@compose(categoryDetailsQuery, categoryDeleteMutation)
class CategoryDescription extends Component {
  static propTypes = {
    pk: PropTypes.number.isRequired,
    data: PropTypes.shape({
      category: PropTypes.shape({
        pk: PropTypes.number,
        name: PropTypes.string,
        description: PropTypes.string,
        parent: PropTypes.shape({
          pk: PropTypes.number
        })
      }),
      loading: PropTypes.bool
    }),
    mutate: PropTypes.func,
    history: PropTypes.object
  };

  constructor(props) {
    super(props);
    this.state = { opened: false };
    this.handleModalOpen = this.handleModalOpen.bind(this);
    this.handleModalClose = this.handleModalClose.bind(this);
    this.handleRemoval = this.handleRemoval.bind(this);
  }

  handleModalOpen() {
    this.setState({ opened: true });
  }

  handleModalClose() {
    this.setState({ opened: false });
  }

  handleRemoval() {
    const { category } = this.props.data;
    const backLink = category.parent ? `/categories/${category.parent.pk}/` : '/categories/';
    this.props.mutate({
      pk: this.props.data.category.pk
    })
      .then(this.handleModalClose)
      .then(() => this.props.history.push(backLink));
  }

  render() {
    return (
      <div>
        {this.props.data.loading && (
          <CircularProgress
            size={80}
            thickness={5}
            color={'secondary'}
          />
        )}
        {!this.props.data.loading && (
          <div>
            <DescriptionCard
              title={this.props.data.category.name}
              description={this.props.data.category.description}
              editButtonHref={`/categories/${this.props.data.category.pk}/edit/`}
              editButtonLabel={pgettext('Category detail view action', 'Edit category')}
              removeButtonLabel={pgettext('Category detail view action', 'Remove category')}
              handleRemoveButtonClick={this.handleModalOpen}
            />
            <ConfirmRemoval
              open={this.state.opened}
              onClose={this.handleModalClose}
              onConfirm={this.handleRemoval}
              content={`Are you sure you want to delete category ${this.props.data.category.name}?`}
            />
          </div>
        )}
      </div>
    );
  }
}

export default CategoryDescription;
