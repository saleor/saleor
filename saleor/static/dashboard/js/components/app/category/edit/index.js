import React, { Component } from 'react';
import PropTypes from 'prop-types';
import gql from 'graphql-tag';
import { graphql } from 'react-apollo';
import CategoryPropertiesForm from '../categoryPropertiesForm';

const query = gql`
  query CategoryDetails($pk: Int!) {
    category(pk: $pk) {
      pk
      name
      description
      parent {
        pk
      }
    }
  }
`;

export default graphql(query, {
  options: (props) => ({
    pk: props.pk
  })
})(() => <CategoryPropertiesForm action="UPDATE"/>);
