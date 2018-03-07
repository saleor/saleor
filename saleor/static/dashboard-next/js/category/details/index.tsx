import * as React from "react";
import Grid from "material-ui/Grid";

import { CategoryProperties } from "./CategoryProperties";
import { CategoryList, RootCategoryList } from "./CategoryList";
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
  <Grid container spacing={24}>
    <Grid item xs={12} md={9}>
      {id ? (
        <Grid container spacing={24}>
          <Grid item xs={12}>
            <CategoryProperties categoryId={id} />
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
);

export default CategoryDetails;
