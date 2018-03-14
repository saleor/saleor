import * as React from "react";
import Avatar from "material-ui/Avatar";
import Button from "material-ui/Button";
import List, {
  ListItemAvatar,
  ListItem,
  ListItemText,
  ListSubheader
} from "material-ui/List";
import Typography from "material-ui/Typography";
import Cached from "material-ui-icons/Cached";
import MoreVert from "material-ui-icons/MoreVert";
import { Link } from "react-router-dom";

import { CategoryPropertiesQuery } from "../gql-types";
import { categoryAddUrl } from "../";
import i18n from "../../i18n";
import Skeleton from "../../components/Skeleton";

interface ProductListProps {
  products?: CategoryPropertiesQuery["category"]["products"]["edges"];
  handleLoadMore();
  canLoadMore: boolean;
}

export const ProductList: React.StatelessComponent<ProductListProps> = ({
  products,
  handleLoadMore,
  canLoadMore
}) => (
  <List>
    {products === undefined ? (
      <ListItem>
        <ListItemAvatar>
          <Avatar>
            <Cached />
          </Avatar>
        </ListItemAvatar>
        <ListItemText>
          <Skeleton />
        </ListItemText>
      </ListItem>
    ) : products.length > 0 ? (
      products.map(edge => (
        <ListItem
          button
          key={edge.node.id}
          component={props => <Link to="#" {...props} />}
        >
          <ListItemAvatar>
            <Avatar src={edge.node.thumbnailUrl} />
          </ListItemAvatar>
          <ListItemText primary={edge.node.name} />
        </ListItem>
      ))
    ) : (
      <ListSubheader>{i18n.t("No products found")}</ListSubheader>
    )}
    {canLoadMore && (
      <ListItem button key="more" onClick={handleLoadMore}>
        <ListItemAvatar>
          <Avatar>
            <MoreVert />
          </Avatar>
        </ListItemAvatar>
        <ListItemText primary={i18n.t("Load more", { context: "button" })} />
      </ListItem>
    )}
  </List>
);

export default ProductList;
