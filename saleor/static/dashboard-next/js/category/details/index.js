import React from 'react';
import PropTypes from 'prop-types';
import Grid from 'material-ui/Grid';

import Details from './details';
import { CategoryList, RootCategoryList } from './categoryList';
import { screenSizes } from '../../misc';
import { SwapChildrenRWD } from '../../components/utils';


// TODO: Plug-in filters
const CategoryDetails = (props) => {
  const categoryId = props.match.params.id;

  return (
    <div>
      <Grid container spacing={16}>
        <SwapChildrenRWD down={screenSizes.md}>
          <Grid item xs={12} md={9}>
            {categoryId ? (
              <div>
                <Details categoryId={categoryId} />
                <CategoryList categoryId={categoryId} />
              </div>
            ) : (
              <RootCategoryList />
            )}
          </Grid>
        </SwapChildrenRWD>
      </Grid>
    </div>
  );
};
CategoryDetails.propTypes = {
  id: PropTypes.string,
  match: PropTypes.object,
};

export default CategoryDetails;
