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
import React from "react";

import TableCellAvatar from "@saleor/components/TableCellAvatar";
import i18n from "@saleor/i18n";
import { maybe, renderCollection } from "@saleor/misc";
import { ListActions, ListProps } from "@saleor/types";
import { CategoryDetails_category_products_edges_node } from "../../categories/types/CategoryDetails";
import Checkbox from "../Checkbox";
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
    settings,
    disabled,
    isChecked,
    pageInfo,
    products,
    selected,
    toggle,
    toggleAll,
    toolbar,
    onNextPage,
    onPreviousPage,
    onUpdateListSettings,
    onRowClick
  }: ProductListProps) => (
    <Table>
      <TableHead
        selected={selected}
        disabled={disabled}
        items={products}
        toggleAll={toggleAll}
        toolbar={toolbar}
      >
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
      </TableHead>
      <TableFooter>
        <TableRow>
          <TablePagination
            colSpan={6}
            settings={settings}
            hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
            onNextPage={onNextPage}
            onUpdateListSettings={onUpdateListSettings}
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
                    checked={isSelected}
                    disabled={disabled}
                    onChange={() => toggle(product.id)}
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
                  {product && maybe(() => product.isAvailable !== undefined) ? (
                    <StatusLabel
                      label={
                        product.isAvailable
                          ? i18n.t("Published", { context: "product status" })
                          : i18n.t("Not published", {
                              context: "product status"
                            })
                      }
                      status={product.isAvailable ? "success" : "error"}
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.colPrice}>
                  {maybe(() => product.basePrice) &&
                  maybe(() => product.basePrice.amount) !== undefined &&
                  maybe(() => product.basePrice.currency) !== undefined ? (
                    <Money money={product.basePrice} />
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
