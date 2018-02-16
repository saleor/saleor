import React from 'react';
import PropTypes from 'prop-types';
import { Route, Switch } from 'react-router-dom';
import Grid from 'material-ui/Grid';

import CategoryEdit from './edit';
import CategoryAdd from './create';
import CategoryDetails from './details';

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
    <Grid container spacing={16}>
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
    </Grid>
  );
};
Component.propTypes = {
  match: PropTypes.object
};

export default Component;
