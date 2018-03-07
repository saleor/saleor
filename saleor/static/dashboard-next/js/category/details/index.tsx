import * as React from "react";
import Grid from "material-ui/Grid";

import Details from "./details";
import { CategoryList, RootCategoryList } from "./categoryList";
import { screenSizes } from "../../misc";

interface CategoryDetailsProps {
  filters: any;
  id: string;
}

// TODO: Plug-in filters
const CategoryDetails: React.StatelessComponent<CategoryDetailsProps> = ({
  filters,
  id
}) => (
  <div>
    <Grid container spacing={24}>
      <Grid item xs={12} md={9}>
        {id ? (
          <Grid container spacing={24}>
            <Grid item xs={12}>
              <Details categoryId={id} />
            </Grid>
            <Grid item xs={12}>
              <CategoryList categoryId={id} filters={filters} />
            </Grid>
          </Grid>
        ) : (
          <RootCategoryList filters={filters} />
        )}
      </Grid>
    </Grid>
  </div>
);

export default CategoryDetails;
