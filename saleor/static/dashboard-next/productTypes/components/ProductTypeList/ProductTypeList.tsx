import Card from "@material-ui/core/Card";
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
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection, translatedTaxRates } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { ProductTypeList_productTypes_edges_node } from "../../types/ProductTypeList";

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colName: {},
      colTax: {
        width: 300
      },
      colType: {
        width: 300
      }
    },
    colName: {},
    colTax: {},
    colType: {},
    link: {
      cursor: "pointer"
    }
  });

interface ProductTypeListProps
  extends ListProps,
    ListActions,
    WithStyles<typeof styles> {
  productTypes: ProductTypeList_productTypes_edges_node[];
}

const ProductTypeList = withStyles(styles, { name: "ProductTypeList" })(
  ({
    classes,
    disabled,
    productTypes,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick,
    isChecked,
    selected,
    toggle,
    toolbar
  }: ProductTypeListProps) => (
    <Card>
      <Table>
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell className={classes.colName}>
              {i18n.t("Type Name", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colType}>
              {i18n.t("Type", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colTax}>
              {i18n.t("Tax", { context: "table header" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={4}
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
            productTypes,
            productType => {
              const isSelected = productType
                ? isChecked(productType.id)
                : false;
              return (
                <TableRow
                  className={!!productType ? classes.link : undefined}
                  hover={!!productType}
                  key={productType ? productType.id : "skeleton"}
                  onClick={productType ? onRowClick(productType.id) : undefined}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(productType.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCell className={classes.colName}>
                    {productType ? (
                      <>
                        {productType.name}
                        <Typography variant="caption">
                          {maybe(() => productType.hasVariants)
                            ? i18n.t("Configurable", {
                                context: "product type"
                              })
                            : i18n.t("Simple product", {
                                context: "product type"
                              })}
                        </Typography>
                      </>
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colType}>
                    {maybe(() => productType.isShippingRequired) !==
                    undefined ? (
                      productType.isShippingRequired ? (
                        <>{i18n.t("Physical", { context: "product type" })}</>
                      ) : (
                        <>{i18n.t("Digital", { context: "product type" })}</>
                      )
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colTax}>
                    {maybe(() => productType.taxRate) ? (
                      translatedTaxRates()[productType.taxRate]
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={4}>
                  {i18n.t("No product types found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
