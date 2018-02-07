import React from 'react';
import PropTypes from 'prop-types';
import { Route, Switch } from 'react-router-dom';

import CategoryEdit from './edit';
import CategoryDetails from './details/index';

const Component = () => {
  const CategoryEditComponent = () => (
    <CategoryEdit pk={this.props.match.params.pk} />
  );
  const CategoryDetailsComponent = () => (
    <CategoryDetails pk={this.props.match.params.pk} />
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
};
Component.propTypes = {
  match: PropTypes.object,
};

export default Component;
