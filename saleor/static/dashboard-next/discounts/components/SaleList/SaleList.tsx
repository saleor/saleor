import Card from "@material-ui/core/Card";
import { createStyles, WithStyles, withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import DateFormatter from "../../../components/DateFormatter";
import Money from "../../../components/Money";
import Percent from "../../../components/Percent";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { SaleType } from "../../../types/globalTypes";
import { SaleList_sales_edges_node } from "../../types/SaleList";

export interface SaleListProps extends ListProps {
  defaultCurrency: string;
  sales: SaleList_sales_edges_node[];
}

const styles = createStyles({
  tableRow: {
    cursor: "pointer"
  },
  textRight: {
    textAlign: "right"
  },
  wideColumn: {
    width: "60%"
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
    sales
  }: SaleListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideColumn}>
              {i18n.t("Name", {
                context: "sale list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Starts", {
                context: "sale list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Ends", {
                context: "sale list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Value", {
                context: "sale list table header"
              })}
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
            sales,
            sale => (
              <TableRow
                className={!!sale ? classes.tableRow : undefined}
                hover={!!sale}
                key={sale ? sale.id : "skeleton"}
              >
                <TableCell
                  className={classes.textRight}
                  onClick={sale ? onRowClick(sale.id) : undefined}
                >
                  {maybe<React.ReactNode>(() => sale.name, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {sale && sale.startDate ? (
                    <DateFormatter date={sale.startDate} />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {sale && sale.endDate ? (
                    <DateFormatter date={sale.endDate} />
                  ) : sale && sale.endDate === null ? (
                    "-"
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell
                  className={classes.textRight}
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
            ),
            () => (
              <TableRow>
                <TableCell colSpan={4}>{i18n.t("No sales found")}</TableCell>
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
