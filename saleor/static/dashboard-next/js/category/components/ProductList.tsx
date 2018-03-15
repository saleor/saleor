import * as React from "react";
import Avatar from "material-ui/Avatar";
import Button from "material-ui/Button";
import List, {
  ListItemAvatar,
  ListItem,
  ListItemText,
  ListSubheader
} from "material-ui/List";
import Table, {
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableRow
} from "material-ui/Table";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import Cached from "material-ui-icons/Cached";
import MoreVert from "material-ui-icons/MoreVert";
import { Link } from "react-router-dom";

import { CategoryPropertiesQuery } from "../gql-types";
import { categoryAddUrl } from "../";
import i18n from "../../i18n";
import Skeleton from "../../components/Skeleton";
import TablePagination from "../../components/TablePagination";

const decorate = withStyles(theme => ({
  avatarCell: {
    paddingRight: 0,
    width: theme.spacing.unit * 5
  }
}));

interface ProductListProps {
  products?: CategoryPropertiesQuery["category"]["products"]["edges"];
  onNextPage();
  onPreviousPage();
  hasNextPage?: boolean;
  hasPreviousPage?: boolean;
}

export const ProductList = decorate<ProductListProps>(
  ({
    classes,
    hasNextPage,
    hasPreviousPage,
    onNextPage,
    onPreviousPage,
    products
  }) => (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell className={classes.avatarCell} />
          <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
          <TableCell>{i18n.t("Type", { context: "object" })}</TableCell>
        </TableRow>
      </TableHead>
      <TableFooter>
        <TableRow>
          <TablePagination
            colSpan={3}
            hasNextPage={hasNextPage}
            onNextPage={onNextPage}
            hasPreviousPage={hasPreviousPage}
            onPreviousPage={onPreviousPage}
          />
        </TableRow>
      </TableFooter>
      <TableBody>
        {products === undefined ? (
          <TableRow>
            <TableCell className={classes.avatarCell}>
              <Avatar>
                <Cached />
              </Avatar>
            </TableCell>
            <TableCell>
              <Skeleton />
            </TableCell>
            <TableCell>
              <Skeleton />
            </TableCell>
          </TableRow>
        ) : products.length > 0 ? (
          products.map(edge => (
            <TableRow key={edge.node.id}>
              <TableCell className={classes.avatarCell}>
                <Avatar src={edge.node.thumbnailUrl} />
              </TableCell>
              <TableCell>{edge.node.name}</TableCell>
              <TableCell>{edge.node.productType.name}</TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell className={classes.avatarCell} />
            <TableCell colSpan={2}>{i18n.t("No products found")}</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  )
);

export default ProductList;
