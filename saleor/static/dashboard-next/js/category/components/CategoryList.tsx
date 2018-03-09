import * as React from "react";
import Typography from "material-ui/Typography";
import Grid from "material-ui/Grid";
import Button from "material-ui/Button";
import { Link } from "react-router-dom";

import { CategoryChildElement } from "./CategoryChildElement";
import { categoryAddUrl, categoryShowUrl } from "../";
import { CategoryPropertiesQuery } from "../gql-types";
import i18n from "../../i18n";

interface CategoryListProps {
  loading?: boolean;
  categories: CategoryPropertiesQuery["category"]["children"]["edges"];
  label: string;
  parentId: string;
}
export const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  loading,
  categories,
  label,
  parentId
}) => (
  <>
    <Typography variant={"display1"}>{label}</Typography>
    <Button
      color="primary"
      component={props => <Link to={categoryAddUrl(parentId)} {...props} />}
      disabled={loading}
    >
      {i18n.t("Add category", { context: "button" })}
    </Button>
    <Grid container>
      {loading ? (
        <CategoryChildElement loading={true} label={""} url={""} />
      ) : (
        <>
          {categories.length > 0 ? (
            <>
              {categories.map(edge => (
                <CategoryChildElement
                  url={categoryShowUrl(edge.node.id)}
                  label={edge.node.name}
                  key={edge.node.id}
                />
              ))}
            </>
          ) : (
            <Typography variant="headline">
              {i18n.t("No categories found")}
            </Typography>
          )}
        </>
      )}
    </Grid>
  </>
);
