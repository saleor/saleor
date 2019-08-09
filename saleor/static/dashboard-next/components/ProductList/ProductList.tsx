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

import TableCellAvatar, {
  AVATAR_MARGIN
} from "@saleor/components/TableCellAvatar";
import { ProductListColumns } from "@saleor/config";
import i18n from "@saleor/i18n";
import { maybe, renderCollection } from "@saleor/misc";
import { ListActions, ListProps } from "@saleor/types";
import { isSelected } from "@saleor/utils/lists";
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
        width: "auto"
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
    colFill: {
      padding: 0,
      width: "100%"
    },
    colName: {},
    colNameHeader: {
      marginLeft: AVATAR_MARGIN
    },
    colPrice: {
      textAlign: "right"
    },
    colPublished: {},
    colType: {},
    link: {
      cursor: "pointer"
    },
    table: {
      tableLayout: "fixed"
    },
    tableContainer: {
      overflowX: "scroll"
    },
    textLeft: {
      textAlign: "left"
    },
    textRight: {
      textAlign: "right"
    }
  });

interface ProductListProps
  extends ListProps<ProductListColumns>,
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
  }: ProductListProps) => {
    const displayColumn = React.useCallback(
      (column: ProductListColumns) =>
        isSelected(column, settings.columns, (a, b) => a === b),
      [settings.columns]
    );
    const numberOfColumns = 2 + settings.columns.length;

    return (
      <div className={classes.tableContainer}>
        <Table className={classes.table}>
          <col />
          <col className={classes.colName} />
          {displayColumn("productType") && <col className={classes.colType} />}
          {displayColumn("isPublished") && (
            <col className={classes.colPublished} />
          )}
          {displayColumn("price") && <col className={classes.colPrice} />}
          <TableHead
            colSpan={numberOfColumns}
            selected={selected}
            disabled={disabled}
            items={products}
            toggleAll={toggleAll}
            toolbar={toolbar}
          >
            <TableCell className={classes.colName}>
              <span className={classes.colNameHeader}>
                {i18n.t("Name", { context: "object" })}
              </span>
            </TableCell>
            {displayColumn("productType") && (
              <TableCell className={classes.colType}>
                {i18n.t("Type", { context: "object" })}
              </TableCell>
            )}
            {displayColumn("isPublished") && (
              <TableCell className={classes.colPublished}>
                {i18n.t("Published", { context: "object" })}
              </TableCell>
            )}
            {displayColumn("price") && (
              <TableCell className={classes.colPrice}>
                {i18n.t("Price", { context: "object" })}
              </TableCell>
            )}
          </TableHead>
          <TableFooter>
            <TableRow>
              <TablePagination
                colSpan={numberOfColumns}
                settings={settings}
                hasNextPage={
                  pageInfo && !disabled ? pageInfo.hasNextPage : false
                }
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
                        disableClickPropagation
                        onChange={() => toggle(product.id)}
                      />
                    </TableCell>
                    <TableCellAvatar
                      className={classes.colName}
                      thumbnail={maybe(() => product.thumbnail.url)}
                    >
                      {product ? product.name : <Skeleton />}
                    </TableCellAvatar>
                    {displayColumn("productType") && (
                      <TableCell className={classes.colType}>
                        {product && product.productType ? (
                          product.productType.name
                        ) : (
                          <Skeleton />
                        )}
                      </TableCell>
                    )}
                    {displayColumn("isPublished") && (
                      <TableCell className={classes.colPublished}>
                        {product &&
                        maybe(() => product.isAvailable !== undefined) ? (
                          <StatusLabel
                            label={
                              product.isAvailable
                                ? i18n.t("Published", {
                                    context: "product status"
                                  })
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
                    )}
                    {displayColumn("price") && (
                      <TableCell className={classes.colPrice}>
                        {maybe(() => product.basePrice) &&
                        maybe(() => product.basePrice.amount) !== undefined &&
                        maybe(() => product.basePrice.currency) !==
                          undefined ? (
                          <Money money={product.basePrice} />
                        ) : (
                          <Skeleton />
                        )}
                      </TableCell>
                    )}
                  </TableRow>
                );
              },
              () => (
                <TableRow>
                  <TableCell colSpan={numberOfColumns}>
                    {i18n.t("No products found")}
                  </TableCell>
                </TableRow>
              )
            )}
          </TableBody>
        </Table>
      </div>
    );
  }
);
ProductList.displayName = "ProductList";
export default ProductList;
