import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
import { graphql, compose } from 'react-apollo';
import { withRouter } from 'react-router-dom';

import { ConfirmRemoval } from '../../../components/modals';
import { DescriptionCard } from '../../../components/cards';
import { categoryDelete } from '../mutations';
import { categoryDetails } from '../queries';

const categoryDetailsQueryFeeder = graphql(categoryDetails, {
  options: props => ({
    variables: {
      id: props.categoryId,
    },
  }),
});
const categoryRemoveMutationFeeder = graphql(categoryDelete);

@withRouter
@compose(categoryDetailsQueryFeeder, categoryRemoveMutationFeeder)
class CategoryProperties extends Component {
  static propTypes = {
    categoryId: PropTypes.string,
    data: PropTypes.shape({
      category: PropTypes.shape({
        parent: PropTypes.shape({
          id: PropTypes.string,
        }),
      }),
    }),
    history: PropTypes.object,
    mutate: PropTypes.func,
  };

  constructor(props) {
    super(props);
    this.handleRemoveButtonClick = this.handleRemoveButtonClick.bind(this);
    this.handleRemoveAction = this.handleRemoveAction.bind(this);
    this.state = { opened: false };
  }

  handleRemoveButtonClick() {
    this.setState(prevState => ({ opened: !prevState.opened }));
  }

  handleRemoveAction() {
    this.props.mutate({
      variables: {
        id: this.props.categoryId,
      },
    })
      .then(() => this.props.history.push(`/categories/${this.props.data.category.parent ? this.props.data.category.parent.id : ''}/`));
  }

  render() {
    const { categoryId, data } = this.props;
    const titleFmt = pgettext('Remove category modal title', 'Remove category %s');
    const contentFmt = pgettext('Remove category modal title', 'Are you sure you want to remove category <strong>%s</strong>?');
    return (
      <div>
        {data.loading ? (
          <span>loading</span>
        ) : (
          <Fragment>
            <DescriptionCard
              title={data.category.name}
              description={data.category.description}
              editButtonHref={`/categories/${categoryId}/edit`}
              editButtonLabel={pgettext('Category edit action', 'Edit')}
              removeButtonLabel={pgettext('Category list action link', 'Remove')}
              handleRemoveButtonClick={this.handleRemoveButtonClick}
            />
            <ConfirmRemoval
              opened={this.state.opened}
              title={interpolate(titleFmt, [data.category.name])}
              onConfirm={this.handleRemoveAction}
              onClose={this.handleRemoveButtonClick}
            >
              <p dangerouslySetInnerHTML={{ __html: interpolate(contentFmt, [data.category.name]) }} />
              {data.category.products && data.category.products.totalCount > 0 && (
                <p>
                  {interpolate(ngettext(
                      'There is one product in this category that will be removed.',
                      'There are %s products in this category that will be removed.',
                      data.category.products.totalCount,
                    ), [data.category.products.totalCount])}
                </p>
              )}
            </ConfirmRemoval>
          </Fragment>
        )}
      </div>
    );
  }
}

export default CategoryProperties;
