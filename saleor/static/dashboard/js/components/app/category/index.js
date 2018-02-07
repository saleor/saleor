import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Route, Switch } from 'react-router-dom';

import CategoryEdit from './edit';
import CategoryDetails from './details/index';

class CategorySection extends Component {
  static propTypes = {
    match: PropTypes.object
  };

  constructor(props) {
    super(props);
    this.state = { loading: true };
  }

  setLoadingStatus(status) {
    this.setState({ loading: status });
  }

  render() {
    const CategoryEditComponent = () => (
      <CategoryEdit
        pk={this.props.match.params.pk}
        setLoadingStatus={this.setLoadingStatus}
      />
    );
    const CategoryDetailsComponent = () => (
      <CategoryDetails
        pk={this.props.match.params.pk}
        setLoadingStatus={this.setLoadingStatus}
      />
    );

    return (
      <div>
        <Switch>
          <Route
            exact
            path={'/categories/:pk/edit'}
            component={CategoryEditComponent}
          />
          <Route
            exact
            path={'/categories/:pk/add'}
            component={CategoryEdit}
          />
          <Route
            exact
            path={'/categories/add'}
            component={CategoryEdit}
          />
          <Route
            exact
            path={'/categories/:pk'}
            component={CategoryDetailsComponent}
          />
          <Route
            exact
            path={'/categories'}
            component={CategoryDetailsComponent}
          />
        </Switch>
      </div>
    );
  }
}

export default CategorySection;
