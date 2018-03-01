import React from 'react';
import { Route, Switch } from 'react-router-dom';

import CategoryDetails from './details';
import { CategoryCreateForm, CategoryUpdateForm } from './form';

const Component = () => (
  <Switch>
    <Route
      exact
      path="/categories/add"
      render={CategoryCreateForm}
    />
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

export default Component;
