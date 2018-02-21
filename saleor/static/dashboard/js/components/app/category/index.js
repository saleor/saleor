import React from 'react';
import PropTypes from 'prop-types';
import { Route, Switch } from 'react-router-dom';

// import CategoryEdit from './edit';
import { CategoryCreateForm } from './form';
import CategoryDetails from './details';

const Component = (props) => {
  const id = props.match.params.id;
  // const CategoryEditComponent = () => (
  //   <CategoryEdit categoryId={id} />
  // );
  // const CategoryAddComponent = () => (
  //   <CategoryAdd categoryId={id} />
  // );

  return (
    <Switch>
      {/*<Route*/}
        {/*exact*/}
        {/*path={'/categories/:id/edit'}*/}
        {/*render={CategoryEditComponent}*/}
      {/*/>*/}
      <Route
        exact
        path={'/categories/:id/add'}
        render={CategoryCreateForm}
      />
      <Route
        exact
        path={'/categories/:id'}
        render={CategoryDetails}
      />
      <Route
        path={'/categories/'}
        render={CategoryDetails}
      />
    </Switch>
  );
};
Component.propTypes = {
  match: PropTypes.object
};

export default Component;
