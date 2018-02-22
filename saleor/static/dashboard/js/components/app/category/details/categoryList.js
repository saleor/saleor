import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { graphql } from 'react-apollo';
import { parse as parseQs } from 'qs';

import { categoryChildren, rootCategoryChildren } from '../queries';
import { ListCard } from '../../../components/cards';
import { createQueryString } from '../../../utils';

const tableHeaders = [
  {
    name: 'name',
    label: 'Name',
  },
  {
    name: 'description',
    label: 'Description',
    wide: true,
  }
];
const PAGINATE_BY = 5;

const feederOptions = {
  options: (props) => {
    const qs = parseQs(props.location.search.substr(1));
    const options = {
      variables: {
        id: props.categoryId
      },
      fetchPolicy: 'network-only'
    };
    let variables;
    switch (qs.action) {
      case 'prev':
        variables = {
          last: parseInt(qs.rowsPerPage) || PAGINATE_BY,
          before: qs.firstCursor,
          first: null,
          after: null
        };
        break;
      case 'next':
        variables = {
          first: parseInt(qs.rowsPerPage) || PAGINATE_BY,
          after: qs.lastCursor,
          last: null,
          before: null
        };
        break;
      default:
        variables = {
          first: parseInt(qs.rowsPerPage) || PAGINATE_BY,
          after: qs.lastCursor,
          last: null,
          before: null
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
  handleAddAction = () => {
    this.props.history.push('add');
  };
  handleChangePage = (firstCursor, lastCursor) => {
    return (event, currentPage) => {
      const prevPage = parseQs(this.props.location.search.substr(1)).currentPage || 0;
      const action = (parseInt(prevPage) < parseInt(currentPage)) ? 'next' : 'prev';
      this.props.history.push({
        search: createQueryString(this.props.location.search, {
          firstCursor,
          lastCursor,
          currentPage,
          action
        })
      });
    };
  };
  handleChangeRowsPerPage = (event) => {
    this.props.history.push({
      search: createQueryString(this.props.location.search, {
        rowsPerPage: event.target.value,
        firstCursor: null,
        lastCursor: null,
        currentPage: 0,
        action: 'next'
      })
    });
  };
}

@withRouter
@categoryListFeeder
class CategoryList extends BaseCategoryList {
  render() {
    const { data } = this.props;
    const categories = data.category ? data.category.children : [];
    const qs = parseQs(this.props.location.search.substr(1));
    const firstCursor = (!data.loading && categories.edges.length) ? categories.edges[0].cursor : '';
    const lastCursor = (!data.loading && categories.edges.length) ? categories.edges.slice(-1)[0].cursor : '';
    return (
      <div>
        {data.loading ? (
          <span>loading</span>
        ) : (
          <ListCard
            displayLabel={true}
            label={pgettext('Category list card title', 'Subcategories')}
            addActionLabel={pgettext('Category list add category action', 'Add category')}
            headers={tableHeaders}
            list={categories.edges.map(edge => edge.node)}
            handleAddAction={this.handleAddAction}
            handleChangePage={this.handleChangePage}
            handleChangeRowsPerPage={this.handleChangeRowsPerPage}
            page={parseInt(qs.currentPage) || 0}
            rowsPerPage={parseInt(qs.rowsPerPage) || PAGINATE_BY}
            count={categories.totalCount}
            firstCursor={firstCursor}
            lastCursor={lastCursor}
            noDataLabel={pgettext('Category list no categories found', 'No categories found')}
          />
        )}
      </div>
    );
  }
}

@withRouter
@rootCategoryListFeeder
class RootCategoryList extends BaseCategoryList {
  render() {
    const { data } = this.props;
    const qs = parseQs(this.props.location.search.substr(1));
    const firstCursor = (!data.loading && data.categories.edges.length) ? data.categories.edges[0].cursor : '';
    const lastCursor = (!data.loading && data.categories.edges.length) ? data.categories.edges.slice(-1)[0].cursor : '';
    return (
      <div>
        {data.loading ? (
          <span>loading</span>
        ) : (
          <ListCard
            displayLabel={false}
            headers={tableHeaders}
            list={data.categories.edges.map(edge => edge.node)}
            handleChangePage={this.handleChangePage}
            handleChangeRowsPerPage={this.handleChangeRowsPerPage}
            page={parseInt(qs.currentPage) || 0}
            rowsPerPage={parseInt(qs.rowsPerPage) || PAGINATE_BY}
            count={data.categories.totalCount}
            firstCursor={firstCursor}
            lastCursor={lastCursor}
            noDataLabel={pgettext('Category list no categories found', 'No categories found')}
          />
        )}
      </div>
    );
  }
}

export {
  CategoryList,
  RootCategoryList
};
