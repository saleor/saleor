import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { CategoryDetails_category_products_edges_node } from "../../categories/types/CategoryDetails";
import TableCellAvatar from "../../components/TableCellAvatar";
import i18n from "../../i18n";
import { renderCollection } from "../../misc";
import { ListProps } from "../../types";
import Money from "../Money";
import Skeleton from "../Skeleton";
import StatusLabel from "../StatusLabel";
import TablePagination from "../TablePagination";

const styles = (theme: Theme) =>
  createStyles({
    avatarCell: {
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: 0,
      width: theme.spacing.unit * 5
    },
    link: {
      cursor: "pointer"
    },
    textLeft: {
      textAlign: "left"
    },
    textRight: {
      textAlign: "right"
    }
  });

interface ProductListProps extends ListProps, WithStyles<typeof styles> {
  products: CategoryDetails_category_products_edges_node[];
}

export const ProductList = withStyles(styles, { name: "ProductList" })(
  ({
    classes,
    disabled,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick,
    products
  }: ProductListProps) => (
    <Table>
      <TableHead>
        <TableRow>
          {(products === undefined || products.length > 0) && <TableCell />}
          <TableCell className={classes.textLeft}>
            {i18n.t("Name", { context: "object" })}
          </TableCell>
          <TableCell>{i18n.t("Type", { context: "object" })}</TableCell>
          <TableCell>{i18n.t("Published", { context: "object" })}</TableCell>
          <TableCell className={classes.textRight}>
            {i18n.t("Price", { context: "object" })}
          </TableCell>
        </TableRow>
      </TableHead>
      <TableFooter>
        <TableRow>
          <TablePagination
            colSpan={5}
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
        {renderCollection(
          products,
          product => (
            <TableRow
              hover={!!product}
              key={product ? product.id : "skeleton"}
              onClick={product && onRowClick(product.id)}
              className={classes.link}
            >
              <TableCellAvatar thumbnail={product && product.thumbnailUrl} />
              <TableCell className={classes.textLeft}>
                {product ? product.name : <Skeleton />}
              </TableCell>
              <TableCell>
                {product && product.productType ? (
                  product.productType.name
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell>
                {product &&
                product.availability &&
                product.availability.available !== undefined ? (
                  <StatusLabel
                    label={
                      product.availability.available
                        ? i18n.t("Published", { context: "product status" })
                        : i18n.t("Not published", { context: "product status" })
                    }
                    status={
                      product.availability.available ? "success" : "error"
                    }
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell className={classes.textRight}>
                {product &&
                product.price &&
                product.price.amount !== undefined &&
                product.price.currency !== undefined ? (
                  <Money money={product.price} />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
            </TableRow>
          ),
          () => (
            <TableRow>
              <TableCell colSpan={5}>{i18n.t("No products found")}</TableCell>
            </TableRow>
          )
        )}
      </TableBody>
    </Table>
  )
);
ProductList.displayName = "ProductList";
export default ProductList;
