import React from 'react';
import PropTypes from 'prop-types';
import MediaQuery from 'react-responsive';
import Grid from 'material-ui/Grid';

import Description from './description';
import Subcategories from './subcategoryList';
import { screenSizes } from '../../../misc';

const CategoryDetails = (props) => (
  <div>
    <MediaQuery minWidth={screenSizes.md}>
      <div>
        <Grid item xs={12} sm={12} md={9} lg={9}>
          {props.pk && (
            <Description pk={props.pk} />
          )}
          <Subcategories pk={props.pk} />
        </Grid>
        <Grid item xs={12} sm={12} md={3} lg={3}>
          sd
        </Grid>
      </div>
    </MediaQuery>
    <MediaQuery maxWidth={screenSizes.md}>
      <div>
        <Grid item xs={12} sm={12} md={3} lg={3}>
          sd
        </Grid>
        <Grid item xs={12} sm={12} md={9} lg={9}>
          {props.pk && (
            <Description pk={props.pk} />
          )}
          <Subcategories pk={props.pk} />
        </Grid>
      </div>
    </MediaQuery>
  </div>
);
CategoryDetails.propTypes = {
  pk: PropTypes.int
};

export default CategoryDetails;
