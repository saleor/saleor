import React from 'react';
import PropTypes from 'prop-types';
import CategoryPropertiesForm from './categoryPropertiesForm';

const component = (props) => (
  <CategoryPropertiesForm
    data={{
      category: {
        name: '',
        description: '',
        pk: null,
        parent: {
          pk: props.pk
        },
        loading: false
      }
    }}
    action="CREATE"
  />
);
component.propTypes = {
  data: PropTypes.shape({
    category: PropTypes.shape({
      pk: PropTypes.number,
      name: PropTypes.string,
      description: PropTypes.string,
      parent: PropTypes.shape({
        pk: PropTypes.number
      })
    }),
    loading: PropTypes.bool
  }),
  action: PropTypes.string,
  pk: PropTypes.int
};
export default component;
