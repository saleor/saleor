import Checkbox from "@material-ui/core/Checkbox";
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
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { CategoryDetails_category_products_edges_node } from "../../categories/types/CategoryDetails";
import TableCellAvatar from "../../components/TableCellAvatar";
import i18n from "../../i18n";
import { maybe, renderCollection } from "../../misc";
import { ListActions, ListProps } from "../../types";
import Money from "../Money";
import Skeleton from "../Skeleton";
import StatusLabel from "../StatusLabel";
import TableHead from "../TableHead";
import TablePagination from "../TablePagination";

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colName: {
        width: 430
      },
      colPrice: {
        width: 200
      },
      colPublished: {
        width: 200
      },
      colType: {
        width: 200
      }
    },
    avatarCell: {
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: 0,
      width: theme.spacing.unit * 5
    },
    colName: {},
    colPrice: {
      textAlign: "right"
    },
    colPublished: {},
    colType: {},
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

interface ProductListProps
  extends ListProps,
    ListActions,
    WithStyles<typeof styles> {
  products: CategoryDetails_category_products_edges_node[];
}

export const ProductList = withStyles(styles, { name: "ProductList" })(
  ({
    classes,
    disabled,
    isChecked,
    pageInfo,
    products,
    selected,
    toggle,
    toolbar,
    onNextPage,
    onPreviousPage,
    onRowClick
  }: ProductListProps) => (
    <Table>
      <TableHead selected={selected} toolbar={toolbar}>
        <TableRow>
          <TableCell />
          <TableCell />
          <TableCell className={classes.colName}>
            {i18n.t("Name", { context: "object" })}
          </TableCell>
          <TableCell className={classes.colType}>
            {i18n.t("Type", { context: "object" })}
          </TableCell>
          <TableCell className={classes.colPublished}>
            {i18n.t("Published", { context: "object" })}
          </TableCell>
          <TableCell className={classes.colPrice}>
            {i18n.t("Price", { context: "object" })}
          </TableCell>
        </TableRow>
      </TableHead>
      <TableFooter>
        <TableRow>
          <TablePagination
            colSpan={6}
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
          product => {
            const isSelected = product ? isChecked(product.id) : false;

            return (
              <TableRow
                selected={isSelected}
                hover={!!product}
                key={product ? product.id : "skeleton"}
                onClick={product && onRowClick(product.id)}
                className={classes.link}
              >
                <TableCell padding="checkbox">
                  <Checkbox
                    color="primary"
                    checked={isSelected}
                    disabled={disabled}
                    onClick={event => {
                      toggle(product.id);
                      event.stopPropagation();
                    }}
                  />
                </TableCell>
                <TableCellAvatar
                  thumbnail={maybe(() => product.thumbnail.url)}
                />
                <TableCell className={classes.colName}>
                  {product ? product.name : <Skeleton />}
                </TableCell>
                <TableCell className={classes.colType}>
                  {product && product.productType ? (
                    product.productType.name
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.colPublished}>
                  {product &&
                  product.availability &&
                  product.availability.available !== undefined ? (
                    <StatusLabel
                      label={
                        product.availability.available
                          ? i18n.t("Published", { context: "product status" })
                          : i18n.t("Not published", {
                              context: "product status"
                            })
                      }
                      status={
                        product.availability.available ? "success" : "error"
                      }
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.colPrice}>
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
            );
          },
          () => (
            <TableRow>
              <TableCell colSpan={6}>{i18n.t("No products found")}</TableCell>
            </TableRow>
          )
        )}
      </TableBody>
    </Table>
  )
);
ProductList.displayName = "ProductList";
export default ProductList;
