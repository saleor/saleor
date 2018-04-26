import Cached from "@material-ui/icons/Cached";
import Avatar from "material-ui/Avatar";
import blue from "material-ui/colors/blue";
import { withStyles } from "material-ui/styles";
import Table, {
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableRow
} from "material-ui/Table";
import * as React from "react";

import { CategoryPropertiesQuery } from "../../gql-types";
import i18n from "../../i18n";
import Skeleton from "../Skeleton";
import TablePagination from "../TablePagination";

const decorate = withStyles(theme => ({
  avatarCell: {
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: 0,
    width: theme.spacing.unit * 5
  },
  link: {
    color: blue[500],
    cursor: "pointer"
  }
}));

interface ProductListProps {
  hasNextPage?: boolean;
  hasPreviousPage?: boolean;
  products?: Array<{
    id: string;
    name: string;
    productType: {
      name: string;
    };
    thumbnailUrl: string;
  }>;
  onNextPage();
  onPreviousPage();
  onRowClick?(id: string);
}

export const ProductList = decorate<ProductListProps>(
  ({
    classes,
    hasNextPage,
    hasPreviousPage,
    onNextPage,
    onPreviousPage,
    onRowClick,
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
        {products === undefined || products === null ? (
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
          products.map(product => (
            <TableRow key={product.id}>
              <TableCell className={classes.avatarCell}>
                <Avatar src={product.thumbnailUrl} />
              </TableCell>
              <TableCell>
                <span
                  onClick={onRowClick ? onRowClick(product.id) : () => {}}
                  className={onRowClick ? classes.link : ""}
                >
                  {product.name}
                </span>
              </TableCell>
              <TableCell>{product.productType.name}</TableCell>
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
