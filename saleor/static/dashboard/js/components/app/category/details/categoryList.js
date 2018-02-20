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
    label: 'Description'
  }
];

function handleChangePage(firstCursor, lastCursor) {
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
}

function handleChangeRowsPerPage(event) {
  this.props.history.push({
    search: createQueryString(this.props.location.search, {
      rowsPerPage: event.target.value,
      firstCursor: null,
      lastCursor: null,
      currentPage: 0,
      action: 'next'
    })
  });
}

const CategoryListComponent = (props) => {
  return (
    <div>xd</div>
  );
};
const CategoryList = withRouter(graphql(categoryChildren, {
  options: {
    variables: (props) => {
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
            last: qs.rowsPerPage || 2,
            before: qs.lastCursor,
            first: null,
            after: null
          };
          break;
        case 'next':
          variables = {
            first: qs.rowsPerPage || 2,
            after: qs.firstCursor,
            last: null,
            before: null
          };
          break;
        default:
          variables = {
            first: qs.rowsPerPage || 2,
            after: qs.firstCursor,
            last: null,
            before: null
          };
          break;
      }
      options.variables = Object.assign({}, options.variables, variables);
      return options;
    }
  }
})(CategoryListComponent));

class RootCategoryListComponent extends Component {
  constructor(props) {
    super(props);
    this.handleChangePage = handleChangePage.bind(this);
    this.handleChangeRowsPerPage = handleChangeRowsPerPage.bind(this);
  }

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
            rowsPerPage={qs.rowsPerPage || 2}
            count={data.categories.totalCount}
            firstCursor={firstCursor}
            lastCursor={lastCursor}
          />
        )}
      </div>
    );
  }
}

const RootCategoryList = withRouter(graphql(rootCategoryChildren, {
  options: (props) => {
    const qs = parseQs(props.location.search.substr(1));
    const options = {
      variables: {},
      fetchPolicy: 'network-only'
    };
    let variables;
    switch (qs.action) {
      case 'prev':
        variables = {
          last: parseInt(qs.rowsPerPage) || 2,
          before: qs.firstCursor,
          first: null,
          after: null
        };
        break;
      case 'next':
        variables = {
          first: parseInt(qs.rowsPerPage) || 2,
          after: qs.lastCursor,
          last: null,
          before: null
        };
        break;
      default:
        variables = {
          first: parseInt(qs.rowsPerPage) || 2,
          after: qs.lastCursor,
          last: null,
          before: null
        };
        break;
    }
    options.variables = Object.assign({}, options.variables, variables);
    return options;
  }
})(RootCategoryListComponent));

export {
  CategoryList,
  RootCategoryList
};
