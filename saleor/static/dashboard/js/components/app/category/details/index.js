import React from 'react';
import PropTypes from 'prop-types';

import Description from './description';
import Subcategories from './subcategoryList';

const CategoryDetails = (props) => (
  <div>
    {props.pk && (
      <Description
        pk={props.pk}
        setLoadingStatus={props.setLoadingStatus}
      />
    )}
    <Subcategories
      pk={props.pk}
      setLoadingStatus={props.setLoadingStatus}
    />
  </div>
);
CategoryDetails.propTypes = {
  pk: PropTypes.int,
  setLoadingStatus: PropTypes.func.isRequired
};
// CategoryDetails.propTypes = {
//   category: PropTypes.shape({
//     pk: PropTypes.number,
//     name: PropTypes.string,
//     description: PropTypes.string,
//     parent: PropTypes.shape({
//       pk: PropTypes.number
//     })
//   }),
//   categoryChildren: PropTypes.arrayOf(PropTypes.shape({
//     pk: PropTypes.number,
//     name: PropTypes.string,
//     description: PropTypes.string
//   }))
// };

export default CategoryDetails;
