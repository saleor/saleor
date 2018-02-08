import React from 'react';
import PropTypes from 'prop-types';
import { graphql } from 'react-apollo';
import CategoryPropertiesForm from './categoryPropertiesForm';
import { CategoryDetails as query } from './queries';

export default graphql(query, {
  options: (props) => ({
    pk: props.pk
  })
})((props) => <CategoryPropertiesForm {...props} action="UPDATE"/>);
