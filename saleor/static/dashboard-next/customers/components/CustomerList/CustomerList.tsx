import Card from "@material-ui/core/Card";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { ListCustomers_customers_edges_node } from "../../types/ListCustomers";

const styles = createStyles({
  tableRow: {
    cursor: "pointer"
  },
  textCenter: {
    textAlign: "center"
  },
  wideCell: {
    width: "60%"
  }
});

export interface CustomerListProps
  extends ListProps,
    WithStyles<typeof styles> {
  customers: ListCustomers_customers_edges_node[];
}

const CustomerList = withStyles(styles, { name: "CustomerList" })(
  ({
    classes,
    disabled,
    customers,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick
  }: CustomerListProps) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              {i18n.t("Customer Name", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.wideCell}>
              {i18n.t("Customer e-mail", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.textCenter}>
              {i18n.t("Orders", { context: "table header" })}
            </TableCell>
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
          {renderCollection(
            customers,
            customer => (
              <TableRow
                className={!!customer ? classes.tableRow : undefined}
                hover={!!customer}
                key={customer ? customer.id : "skeleton"}
              >
                <TableCell
                  onClick={customer ? onRowClick(customer.id) : undefined}
                >
                  {maybe<React.ReactNode>(
                    () => `${customer.firstName} ${customer.lastName}`,
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {maybe<React.ReactNode>(() => customer.email, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.textCenter}>
                  {maybe<React.ReactNode>(
                    () => customer.orders.totalCount,
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>
                  {i18n.t("No customers found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
CustomerList.displayName = "CustomerList";
export default CustomerList;
