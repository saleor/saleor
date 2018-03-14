import * as React from "react";
import Typography from "material-ui/Typography";
import Grid from "material-ui/Grid";
import Button from "material-ui/Button";
import { Link } from "react-router-dom";

import CategoryChildElement from "./CategoryChildElement";
import { categoryAddUrl, categoryShowUrl } from "../";
import { CategoryPropertiesQuery } from "../gql-types";
import i18n from "../../i18n";

interface CategoryListProps {
  categories?: CategoryPropertiesQuery["category"]["children"]["edges"];
}
export const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  categories
}) => (
  <Grid container>
    {categories === undefined ? (
      <Grid item xs={12} sm={6} md={4} lg={3} xl={2}>
        <CategoryChildElement loading={true} label="" url="" />
      </Grid>
    ) : categories.length > 0 ? (
      categories.map(edge => (
        <Grid item xs={12} sm={6} md={4} lg={3} xl={2}>
          <CategoryChildElement
            url={categoryShowUrl(edge.node.id)}
            label={edge.node.name}
            key={edge.node.id}
          />
        </Grid>
      ))
    ) : (
      <Grid item xs={12}>
        <Typography variant="body2">{i18n.t("No categories found")}</Typography>
      </Grid>
    )}
  </Grid>
);

export default CategoryList;
