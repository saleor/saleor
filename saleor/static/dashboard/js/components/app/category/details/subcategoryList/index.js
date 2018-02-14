import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { parse } from 'qs';

import SubcategoryListCardFeeder from './subcategoryListCardFeeder';

@withRouter
class SubcategoryList extends Component {
  static propTypes = {
    data: PropTypes.shape({
      categories: PropTypes.shape({
        edges: PropTypes.arrayOf(
          PropTypes.shape({
            node: PropTypes.shape({
              pk: PropTypes.number,
              name: PropTypes.string,
              description: PropTypes.string
            })
          })
        )
      }),
      loading: PropTypes.bool
    }),
    pk: PropTypes.number,
    history: PropTypes.object.isRequired,
    classes: PropTypes.object
  };

  constructor(props) {
    super(props);
    const qs = parse(props.location.search.substr(1));
    this.state = {
      currentPage: parseInt(qs.currentPage) || 0,
      rowsPerPage: parseInt(qs.rowsPerPage) || 5,
      action: qs.action || 'next',
      firstCursor: qs.firstCursor,
      lastCursor: qs.lastCursor
    };
    this.handleChangePage = this.handleChangePage.bind(this);
    this.handleChangeRowsPerPage = this.handleChangeRowsPerPage.bind(this);
    this.handleNewCategoryClick = this.handleNewCategoryClick.bind(this);
  }

  handleNewCategoryClick() {
    this.props.history.push('add');
  }

  handleChangePage(firstCursor, lastCursor) {
    return (event, page) => {
      this.setState((prevState) => {
        let action;
        if (prevState.currentPage > page) {
          action = 'prev';
        } else {
          action = 'next';
        }
        return {
          currentPage: page,
          firstCursor,
          lastCursor,
          action
        };
      });
    };
  }

  handleChangeRowsPerPage(event) {
    this.setState({
      rowsPerPage: event.target.value,
      firstCursor: null,
      lastCursor: null,
      currentPage: 0
    });
  }

  render() {
    let cursor;
    switch (this.state.action) {
      case 'prev':
        cursor = this.state.firstCursor;
        break;
      case 'next':
        cursor = this.state.lastCursor;
        break;
    }
    return (
      <SubcategoryListCardFeeder
        pk={this.props.pk}
        page={this.state.currentPage}
        rowsPerPage={this.state.rowsPerPage}
        handleChangeRowsPerPage={this.handleChangeRowsPerPage}
        handleChangePage={this.handleChangePage}
        handleNewCategoryClick={this.handleNewCategoryClick}
        cursor={cursor}
        action={this.state.action}
      />
    );
  }
}

export default SubcategoryList;
