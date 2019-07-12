import Card from "@material-ui/core/Card";
import {
  createStyles,
  Theme,
  WithStyles,
  withStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableRow from "@material-ui/core/TableRow";
import React from "react";

import Checkbox from "@saleor/components/Checkbox";
import Date from "@saleor/components/Date";
import Money from "@saleor/components/Money";
import Percent from "@saleor/components/Percent";
import Skeleton from "@saleor/components/Skeleton";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { SaleType } from "../../../types/globalTypes";
import { SaleList_sales_edges_node } from "../../types/SaleList";

export interface SaleListProps extends ListProps, ListActions {
  defaultCurrency: string;
  sales: SaleList_sales_edges_node[];
}

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colEnd: {
        width: 250
      },
      colName: {},
      colStart: {
        width: 250
      },
      colValue: {
        width: 200
      }
    },
    colEnd: {
      textAlign: "right"
    },
    colName: {},
    colStart: {
      textAlign: "right"
    },
    colValue: {
      textAlign: "right"
    },
    tableRow: {
      cursor: "pointer"
    }
  });

const SaleList = withStyles(styles, {
  name: "SaleList"
})(
  ({
    classes,
    defaultCurrency,
    disabled,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo,
    sales,
    isChecked,
    selected,
    toggle,
    toggleAll,
    toolbar
  }: SaleListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead
          selected={selected}
          disabled={disabled}
          items={sales}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell className={classes.colName}>
            {i18n.t("Name", {
              context: "sale list table header"
            })}
          </TableCell>
          <TableCell className={classes.colStart}>
            {i18n.t("Starts", {
              context: "sale list table header"
            })}
          </TableCell>
          <TableCell className={classes.colEnd}>
            {i18n.t("Ends", {
              context: "sale list table header"
            })}
          </TableCell>
          <TableCell className={classes.colValue}>
            {i18n.t("Value", {
              context: "sale list table header"
            })}
          </TableCell>
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
            sales,
            sale => {
              const isSelected = sale ? isChecked(sale.id) : false;

              return (
                <TableRow
                  className={!!sale ? classes.tableRow : undefined}
                  hover={!!sale}
                  key={sale ? sale.id : "skeleton"}
                  onClick={sale ? onRowClick(sale.id) : undefined}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(sale.id)}
                    />
                  </TableCell>
                  <TableCell className={classes.colName}>
                    {maybe<React.ReactNode>(() => sale.name, <Skeleton />)}
                  </TableCell>
                  <TableCell className={classes.colStart}>
                    {sale && sale.startDate ? (
                      <Date date={sale.startDate} />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colEnd}>
                    {sale && sale.endDate ? (
                      <Date date={sale.endDate} />
                    ) : sale && sale.endDate === null ? (
                      "-"
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell
                    className={classes.colValue}
                    onClick={sale ? onRowClick(sale.id) : undefined}
                  >
                    {sale && sale.type && sale.value ? (
                      sale.type === SaleType.FIXED ? (
                        <Money
                          money={{
                            amount: sale.value,
                            currency: defaultCurrency
                          }}
                        />
                      ) : (
                        <Percent amount={sale.value} />
                      )
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={5}>{i18n.t("No sales found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
SaleList.displayName = "SaleList";
export default SaleList;
