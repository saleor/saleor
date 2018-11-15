import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
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

export interface CustomerListProps extends ListProps {
  customers: ListCustomers_customers_edges_node[];
}

const decorate = withStyles({
  tableRow: {
    cursor: "pointer" as "pointer"
  },
  textRight: {
    textAlign: "right" as "right"
  },
  wideCell: {
    width: "60%"
  }
});
const CustomerList = decorate<CustomerListProps>(
  ({
    classes,
    disabled,
    customers,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideCell}>
              {i18n.t("Customer e-mail", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Orders", { context: "table header" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={2}
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
                  {maybe<React.ReactNode>(() => customer.email, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {maybe<React.ReactNode>(
                    () => customer.orders.totalCount,
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>
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
