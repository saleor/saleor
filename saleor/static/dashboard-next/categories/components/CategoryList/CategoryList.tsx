import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import ListSubheader from "@material-ui/core/ListSubheader";
import AddIcon from "@material-ui/icons/Add";
import Folder from "@material-ui/icons/Folder";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

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
      <PageHeader title={i18n.t("Categories")}>
        {!!onAdd && (
          <IconButton onClick={onAdd}>
            <AddIcon />
          </IconButton>
        )}
      </PageHeader>
    )}
    <List>
      {categories === undefined || categories === null ? (
        <ListItem>
          <ListItemIcon>
            <Folder />
          </ListItemIcon>
          <ListItemText>
            <Skeleton />
          </ListItemText>
        </ListItem>
      ) : categories.length > 0 ? (
        categories.map(category => (
          <ListItem
            button={!!onRowClick}
            key={category.id}
            onClick={!!onRowClick ? onRowClick(category.id) : undefined}
          >
            <ListItemIcon>
              <Folder />
            </ListItemIcon>
            <ListItemText primary={category.name} />
          </ListItem>
        ))
      ) : (
        <ListSubheader>{i18n.t("No categories found")}</ListSubheader>
      )}
    </List>
  </Card>
);
export default CategoryList;
