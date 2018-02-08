import React from 'react';
import PropTypes from 'prop-types';
import { Route, Switch } from 'react-router-dom';

import CategoryEdit from './edit';
import CategoryAdd from './add'
import CategoryDetails from './details/index';

const Component = (props) => {
  const CategoryEditComponent = () => (
    <CategoryEdit pk={props.match.params.pk} />
  );
  const CategoryAddComponent = () => (
    <CategoryAdd pk={props.match.params.pk} />
  );
  const CategoryDetailsComponent = () => (
    <CategoryDetails pk={props.match.params.pk} />
  );

  return (
    <div>
      <Switch>
        <Route
          exact
          path={'/categories/:pk/edit'}
          render={CategoryEditComponent}
        />
        <Route
          exact
          path={'/categories/:pk/add'}
          render={CategoryAddComponent}
        />
        <Route
          exact
          path={'/categories/add'}
          render={CategoryAddComponent}
        />
        <Route
          exact
          path={'/categories/:pk'}
          render={CategoryDetailsComponent}
        />
        <Route
          exact
          path={'/categories'}
          render={CategoryDetailsComponent}
        />
      </Switch>
    </div>
  );
};
Component.propTypes = {
  match: PropTypes.object
};

export default Component;
