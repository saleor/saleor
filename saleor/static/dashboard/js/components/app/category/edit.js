import React from 'react';
import { graphql } from 'react-apollo';
import CategoryPropertiesForm from './categoryPropertiesForm';
import { categoryDetails as query } from './queries';

export default graphql(query, {
  options: (props) => ({
    pk: props.pk
  })
})((props) => <CategoryPropertiesForm {...props} action="UPDATE"/>);
