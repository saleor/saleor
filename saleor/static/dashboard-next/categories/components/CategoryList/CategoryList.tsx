import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import ListSubheader from "@material-ui/core/ListSubheader";
import Folder from "@material-ui/icons/Folder";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface CategoryListProps {
  categories?: Array<{
    id: string;
    name: string;
  }>;
  displayTitle?: boolean;
  onAdd?();
  onRowClick?(id: string): () => void;
}

const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  categories,
  displayTitle,
  onAdd,
  onRowClick
}) => (
  <Card>
    {displayTitle && (
      <CardTitle
        title={i18n.t("Categories")}
        toolbar={
          <Button color="secondary" variant="flat" onClick={onAdd}>
            {i18n.t("Add category")}
          </Button>
        }
      />
    )}
    <List>
      {renderCollection(
        categories,
        category => (
          <ListItem
            button={!!category && !!onRowClick}
            key={category ? category.id : "skeleton"}
            onClick={category && onRowClick && onRowClick(category.id)}
          >
            <ListItemIcon>
              <Folder />
            </ListItemIcon>
            <ListItemText>
              {category ? category.name : <Skeleton />}
            </ListItemText>
          </ListItem>
        ),
        () => (
          <ListSubheader>{i18n.t("No categories found")}</ListSubheader>
        )
      )}
    </List>
  </Card>
);
export default CategoryList;
