import * as React from "react";
import Grid from "material-ui/Grid";

import Details from "./details";
import { CategoryList, RootCategoryList } from "./categoryList";
import { screenSizes } from "../../misc";
import { SwapChildrenRWD } from "../../components/utils";

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
    <Grid container spacing={16}>
      <SwapChildrenRWD down={screenSizes.md}>
        <Grid item xs={12} md={9}>
          {id ? (
            <div>
              <Details categoryId={id} />
              <CategoryList categoryId={id} filters={filters} />
            </div>
          ) : (
            <RootCategoryList filters={filters} />
          )}
        </Grid>
      </SwapChildrenRWD>
    </Grid>
  </div>
);

export default CategoryDetails;
