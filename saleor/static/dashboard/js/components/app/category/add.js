import React, { Component } from 'react';
import PropTypes from 'prop-types';
import CategoryPropertiesForm from './categoryPropertiesForm';

export default (props) => (
  <CategoryPropertiesForm
    data={{
      category: {
        name: '',
        description: '',
        pk: props.pk,
        loading: false
      }
    }}
    action="ADD"
  />
);
