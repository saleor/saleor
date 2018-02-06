import React from 'react';
import PropTypes from 'prop-types';

import Description from './description';
import Subcategories from './subcategoryList';

const CategoryDetails = (props) => (
  <div>
    {props.category && (
      <Description category={props.category} />
    )}
    <Subcategories
      category={props.category}
      categoryChildren={props.categoryChildren}
    />
  </div>
);
CategoryDetails.propTypes = {
  category: PropTypes.shape({
    pk: PropTypes.number,
    name: PropTypes.string,
    description: PropTypes.string,
    parent: PropTypes.shape({
      pk: PropTypes.number
    })
  }),
  categoryChildren: PropTypes.arrayOf(PropTypes.shape({
    pk: PropTypes.number,
    name: PropTypes.string,
    description: PropTypes.string
  }))
};

export default CategoryDetails;
