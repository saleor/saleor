import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { graphql } from 'react-apollo';
import { parse as parseQs } from 'qs';
import { withRouter } from 'react-router-dom';

import { ListCard } from '../../../components/cards';
import { categoryChildren, rootCategoryChildren } from '../queries';
import { createQueryString } from '../../../utils';

const tableHeaders = [
  {
    label: pgettext('Category list table header name', 'Name'),
    name: 'name',
  },
  {
    label: pgettext('Category list table header description', 'Description'),
    name: 'description',
    wide: true,
  }
];
const PAGINATE_BY = 5;

const feederOptions = {
  options: (props) => {
    const options = {
      variables: {
        id: props.categoryId
      },
      fetchPolicy: 'network-only'
    };
    const qs = parseQs(props.location.search.substr(1));
    let variables;
    switch (qs.action) {
      case 'prev':
        variables = {
          after: null,
          before: qs.firstCursor,
          first: null,
          last: parseInt(qs.rowsPerPage) || PAGINATE_BY,
        };
        break;
      case 'next':
        variables = {
          after: qs.lastCursor,
          before: null,
          first: parseInt(qs.rowsPerPage) || PAGINATE_BY,
          last: null,
        };
        break;
      default:
        variables = {
          after: qs.lastCursor,
          before: null,
          first: parseInt(qs.rowsPerPage) || PAGINATE_BY,
          last: null,
        };
        break;
    }
    options.variables = Object.assign({}, options.variables, variables);
    return options;
  }
};
const categoryListFeeder = graphql(categoryChildren, feederOptions);
const rootCategoryListFeeder = graphql(rootCategoryChildren, feederOptions);

class BaseCategoryList extends Component {
  static propTypes = {
    categories: PropTypes.shape({
      edges: PropTypes.array,
      totalCount: PropTypes.number,
    }).isRequired,
    history: PropTypes.object,
    location: PropTypes.object,
    label: PropTypes.string.isRequired,
  };

  handleAddAction = () => {
    this.props.history.push('add');
  };
  handleChangePage = (firstCursor, lastCursor) => {
    return (event, currentPage) => {
      const prevPage = parseQs(this.props.location.search.substr(1)).currentPage || 0;
      const action = (parseInt(prevPage) < parseInt(currentPage)) ? 'next' : 'prev';
      this.props.history.push({
        search: createQueryString(this.props.location.search, {
          action,
          currentPage,
          firstCursor,
          lastCursor,
        })
      });
    };
  };
  handleChangeRowsPerPage = (event) => {
    this.props.history.push({
      search: createQueryString(this.props.location.search, {
        action: 'next',
        currentPage: 0,
        firstCursor: null,
        lastCursor: null,
        rowsPerPage: event.target.value,
      })
    });
  };

  render() {
    const {
      label,
      categories
    } = this.props;
    const firstCursor = categories.edges.length > 0 ? categories.edges[0].cursor : '';
    const lastCursor = categories.edges.length > 0 ? categories.edges.slice(-1)[0].cursor : '';
    const qs = parseQs(this.props.location.search.substr(1));
    return (
      <ListCard
        addActionLabel={gettext('Add')}
        count={categories.totalCount}
        displayLabel={true}
        firstCursor={firstCursor}
        handleAddAction={this.handleAddAction}
        handleChangePage={this.handleChangePage}
        handleChangeRowsPerPage={this.handleChangeRowsPerPage}
        headers={tableHeaders}
        href="/categories"
        label={label}
        lastCursor={lastCursor}
        list={categories.edges.map(edge => edge.node)}
        noDataLabel={pgettext('Empty category list message', 'No categories found.')}
        page={parseInt(qs.currentPage) || 0}
        rowsPerPage={parseInt(qs.rowsPerPage) || PAGINATE_BY}
      />
    );
  }
}

const CategoryListComponent = (props) => {
  const { data } = props;
  const categories = data.category ? data.category.children : [];
  return (
    <div>
      {data.loading ? (
        <span>loading</span>
      ) : (
        <BaseCategoryList
          categories={categories}
          history={props.history}
          label={pgettext('Title of the subcategories list', 'Subcategories')}
          location={props.location}
        />
      )}
    </div>
  );
};
CategoryListComponent.propTypes = {
  data: PropTypes.shape({
    loading: PropTypes.boolean,
    category: PropTypes.shape({
      children: PropTypes.shape({
        edges: PropTypes.array,
        totalCount: PropTypes.number,
      }),
    })
  }),
  history: PropTypes.object,
  location: PropTypes.object
};
const CategoryList = withRouter(categoryListFeeder(CategoryListComponent));

const RootCategoryListComponent = (props) => {
  const { data } = props;
  const categories = data.categories || [];
  return (
    <div>
      {data.loading ? (
        <span>loading</span>
      ) : (
        <BaseCategoryList
          categories={categories}
          history={props.history}
          label={pgettext('Title of the categories list', 'Categories')}
          location={props.location}
        />
      )}
    </div>
  );
};
RootCategoryListComponent.propTypes = {
  data: PropTypes.shape({
    loading: PropTypes.boolean,
    categories: PropTypes.shape({
      edges: PropTypes.array,
      totalCount: PropTypes.number,
    }),
  }),
  history: PropTypes.object,
  location: PropTypes.object
};
const RootCategoryList = withRouter(rootCategoryListFeeder(RootCategoryListComponent));

export {
  CategoryList,
  RootCategoryList
};
