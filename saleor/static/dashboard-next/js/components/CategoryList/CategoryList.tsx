import Folder from "material-ui-icons/Folder";
import List, {
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader
} from "material-ui/List";
import * as React from "react";

import { CategoryPropertiesQuery } from "../../gql-types";
import i18n from "../../i18n";
import Skeleton from "../Skeleton";

interface CategoryListProps {
  categories?: CategoryPropertiesQuery["category"]["children"]["edges"];
  onClick?(id: string);
}
export const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  categories,
  onClick
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
          button={!!onClick}
          key={edge.node.id}
          onClick={
            onClick !== undefined ? () => onClick(edge.node.id) : undefined
          }
        >
          <ListItemIcon>
            <Folder />
          </ListItemIcon>
          <ListItemText primary={edge.node.name} />
        </ListItem>
      ))
    ) : (
      <ListSubheader>{i18n.t("No categories found")}</ListSubheader>
    )}
  </List>
);

export default CategoryList;
