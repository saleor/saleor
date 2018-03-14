import * as React from "react";
import Button from "material-ui/Button";
import Grid from "material-ui/Grid";
import List, {
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader
} from "material-ui/List";
import Typography from "material-ui/Typography";
import Folder from "material-ui-icons/Folder";
import { Link } from "react-router-dom";

import { categoryAddUrl, categoryShowUrl } from "../";
import { CategoryPropertiesQuery } from "../gql-types";
import i18n from "../../i18n";
import Skeleton from "../../components/Skeleton";

interface CategoryListProps {
  categories?: CategoryPropertiesQuery["category"]["children"]["edges"];
}
export const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  categories
}) => (
  <List>
    {categories === undefined ? (
      <ListItem>
        <ListItemIcon>
          <Folder />
        </ListItemIcon>
        <ListItemText>
          <Skeleton />
        </ListItemText>
      </ListItem>
    ) : categories.length > 0 ? (
      categories.map(edge => (
        <ListItem
          button
          key={edge.node.id}
          component={props => (
            <Link to={categoryShowUrl(edge.node.id)} {...props} />
          )}
        >
          <ListItemIcon>
            <Folder />
          </ListItemIcon>
          <ListItemText>{edge.node.name}</ListItemText>
        </ListItem>
      ))
    ) : (
      <ListSubheader>{i18n.t("No categories found")}</ListSubheader>
    )}
  </List>
);

export default CategoryList;
