import React from 'react';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import { Route, Switch } from 'react-router-dom';
import { CircularProgress } from 'material-ui/Progress';

import CategoryEdit from './edit';
import CategoryDetails from './details/index';

const CategorySection = (props) => {
  if (props.data.loading && !props.data.categories) {
    return (
      <CircularProgress size={80} thickness={5} style={{ margin: 'auto' }} />
    );
  } else {
    return (
      <Switch>
        <Route exact path={'/categories/:pk/edit'} render={() => <CategoryEdit category={props.data.category} />} />
        <Route exact path={'/categories/:pk/add'} render={() => <CategoryEdit />} />
        <Route exact path={'/categories'} render={() => <CategoryDetails categoryChildren={props.data.categories} />} />
        <Route exact path={'/categories/add'} render={() => <CategoryEdit />} />
        <Route exact path={'/categories/:pk'} render={() => <CategoryDetails category={props.data.category}
          categoryChildren={props.data.categories} />} />
      </Switch>
    );
  }
};
const query = gql`
query CategoryPage ($pk: Int!) {
  categories(parent: $pk) {
    pk
    name
    description
  }
  category(pk: $pk) {
    pk
    name
    description
    parent {
      pk
    }
  }
}`;
const CategorySectionGraphQLProvider = graphql(query, {
  options: ({ match }) => ({
    variables: {
      pk: match.params.pk || -1
    }
  })
})(CategorySection);

export default CategorySectionGraphQLProvider;
