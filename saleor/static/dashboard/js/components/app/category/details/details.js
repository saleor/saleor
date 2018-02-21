import React, { Component } from 'react';
import { graphql, compose } from 'react-apollo';
import { withRouter } from 'react-router-dom';

import { DescriptionCard } from '../../../components/cards';
import { categoryDetails } from '../queries';
import { categoryDelete } from '../mutations';
import { ConfirmRemoval } from '../../../components/modals';

const categoryDetailsQueryFeeder = graphql(categoryDetails, {
  options: (props) => ({
    variables: {
      id: props.categoryId
    }
  })
});
const categoryRemoveMutationFeeder = graphql(categoryDelete);

@withRouter
@compose(categoryDetailsQueryFeeder, categoryRemoveMutationFeeder)
class CategoryProperties extends Component {
  constructor(props) {
    super(props);
    this.handleRemoveButtonClick = this.handleRemoveButtonClick.bind(this);
    this.handleRemoveAction = this.handleRemoveAction.bind(this);
    this.state = { opened: false };
  }

  handleRemoveButtonClick() {
    this.setState((prevState) => ({ opened: !prevState.opened }));
  }

  handleRemoveAction() {
    this.props.mutate({
      variables: {
        id: this.props.categoryId
      }
    })
      .then(() => this.props.history.push(`/categories/${this.props.data.category.parent ? this.props.data.category.parent.id : ''}/`));
  }

  render() {
    const { categoryId, data } = this.props;
    return (
      <div>
        {data.loading ? (
          <span>loading</span>
        ) : (
          <DescriptionCard
            title={data.category.name}
            description={data.category.description}
            editButtonHref={`/categories/${categoryId}/edit`}
            editButtonLabel={pgettext('Category edit action button label', 'Edit category')}
            removeButtonLabel={pgettext('Category remove action button label', 'Remove category')}
            handleRemoveButtonClick={this.handleRemoveButtonClick}
          />
        )}
        <ConfirmRemoval
          opened={this.state.opened}
          content={'u sure bruh?'}
          onConfirm={this.handleRemoveAction}
          onClose={this.handleRemoveButtonClick}
        />
      </div>
    );
  };
}

export default CategoryProperties;
