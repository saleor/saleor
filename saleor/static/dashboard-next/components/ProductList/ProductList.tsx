import Avatar from "@material-ui/core/Avatar";
import blue from "@material-ui/core/colors/blue";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Cached from "@material-ui/icons/Cached";
import * as React from "react";

import { ListProps } from "../..";
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

interface ProductListProps extends ListProps {
  products?: Array<{
    id: string;
    name: string;
    productType: {
      name: string;
    };
    thumbnailUrl: string;
  }>;
}

export const ProductList = decorate<ProductListProps>(
  ({
    classes,
    disabled,
    pageInfo,
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
            hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
            onNextPage={onNextPage}
            hasPreviousPage={
              pageInfo && !disabled ? pageInfo.hasPreviousPage : false
            }
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
                  onClick={onRowClick ? onRowClick(product.id) : undefined}
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
