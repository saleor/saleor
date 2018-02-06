import React from 'react';
import PropTypes from 'prop-types';

import Description from './description';
import Subcategories from './subcategoryList';

const CategoryDetails = (props) => (
  <div>
    {props.pk && (
      <Description pk={props.pk} />
    )}
    <Subcategories pk={props.pk} />
  </div>
);
CategoryDetails.propTypes = {
  pk: PropTypes.int
};

export default CategoryDetails;
