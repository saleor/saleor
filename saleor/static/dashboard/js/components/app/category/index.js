import React, { Component } from 'react';
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
        <Route path={''} render={() => <CategoryDetails category={props.data.category}
                                                        children={props.data.categories} />} />
        <Route path={'edit'} render={() => <CategoryEdit category={props.data.category} />} />
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
    name
    description
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
