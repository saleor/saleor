import React, { Component } from 'react';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';


class CategorySection extends Component {
  render() {
    if (this.props.data.loading && !this.props.data.categories) {
      return (
        <div>loading</div>
      );
    } else {
      return (
        <div>done</div>
      );
    }
  }
}

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
  options: ({match}) => ({
    variables: {
      pk: match.params.pk || -1
    }
  })
})(CategorySection);

export default CategorySectionGraphQLProvider
