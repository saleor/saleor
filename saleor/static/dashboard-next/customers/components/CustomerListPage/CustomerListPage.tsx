import Card from "@material-ui/core/Card";
import blue from "@material-ui/core/colors/blue";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface CustomerListPageProps extends PageListProps {
  customers?: Array<{
    id: string;
    email: string;
    defaultBillingAddress: {
      firstName: string;
      lastName: string;
      city: string;
      country: string;
    };
  }>;
}

const decorate = withStyles(theme => ({
  link: {
    color: blue[500],
    cursor: "pointer"
  }
}));
const CustomerListPage = decorate<CustomerListPageProps>(
  ({
    classes,
    customers,
    disabled,
    pageInfo,
    onAdd,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Container width="md">
      <PageHeader title={i18n.t("Customers")}>
        <IconButton disabled={disabled} onClick={onAdd}>
          <AddIcon />
        </IconButton>
      </PageHeader>
      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
              <TableCell>{i18n.t("E-mail", { context: "object" })}</TableCell>
              <TableCell>
                {i18n.t("Localization", { context: "object" })}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableFooter>
            <TableRow>
              <TablePagination
                colSpan={3}
                hasNextPage={pageInfo ? pageInfo.hasNextPage : undefined}
                onNextPage={onNextPage}
                hasPreviousPage={
                  pageInfo ? pageInfo.hasPreviousPage : undefined
                }
                onPreviousPage={onPreviousPage}
              />
            </TableRow>
          </TableFooter>
          <TableBody>
            {customers === undefined || customers === null ? (
              <TableRow>
                <TableCell>
                  <Skeleton />
                </TableCell>
                <TableCell>
                  <Skeleton />
                </TableCell>
                <TableCell>
                  <Skeleton />
                </TableCell>
              </TableRow>
            ) : customers.length > 0 ? (
              customers.map(customer => (
                <TableRow key={customer.id}>
                  <TableCell>
                    <span
                      onClick={onRowClick ? onRowClick(customer.id) : undefined}
                      className={onRowClick ? classes.link : ""}
                    >
                      {customer.defaultBillingAddress.firstName}{" "}
                      {customer.defaultBillingAddress.lastName}
                    </span>
                  </TableCell>
                  <TableCell>{customer.email}</TableCell>
                  <TableCell>
                    {customer.defaultBillingAddress.city},{" "}
                    {customer.defaultBillingAddress.country}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={3}>
                  {i18n.t("No customers found")}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </Container>
  )
);
export default CustomerListPage;
