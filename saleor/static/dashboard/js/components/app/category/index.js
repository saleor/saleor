import React from 'react';
import PropTypes from 'prop-types';
import { Route, Switch } from 'react-router-dom';

import { CategoryCreateForm, CategoryUpdateForm } from './form';
import CategoryDetails from './details';

const Component = () => (
  <Switch>
    <Route
      exact
      path="/categories/:id/edit"
      render={CategoryUpdateForm}
    />
    <Route
      exact
      path="/categories/:id/add"
      render={CategoryCreateForm}
    />
    <Route
      exact
      path="/categories/:id"
      render={CategoryDetails}
    />
    <Route
      path="/categories/"
      render={CategoryDetails}
    />
  </Switch>
);
Component.propTypes = {
  match: PropTypes.object,
};

export default Component;
