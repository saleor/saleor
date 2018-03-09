import * as React from "react";
import Typography from "material-ui/Typography";
import Grid from "material-ui/Grid";
import Button from "material-ui/Button";
import { Link } from "react-router-dom";
import { gettext, pgettext } from "../../i18n";
import { categoryAddUrl } from "../";

import { CategoryChildElement } from "./CategoryChildElement";
import { categoryShowUrl } from "../";
import { CategoryPropertiesQuery } from "../gql-types";

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
      {gettext("Add category")}
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
              {pgettext(
                "Dashboard categories no categories found",
                "No categories found"
              )}
            </Typography>
          )}
        </>
      )}
    </Grid>
  </>
);
