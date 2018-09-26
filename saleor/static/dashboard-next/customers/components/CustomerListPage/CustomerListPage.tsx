import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
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
import { renderCollection } from "../../../misc";

interface CustomerListPageProps extends PageListProps {
  customers?: Array<{
    id: string;
    email: string;
    defaultBillingAddress: {
      firstName: string;
      lastName: string;
      city: string;
      country: {
        code: string;
        country: string;
      };
    };
  }>;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
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
        <Button
          color="secondary"
          variant="contained"
          disabled={disabled}
          onClick={onAdd}
        >
          {i18n.t("Add customer")} <AddIcon />
        </Button>
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
            {renderCollection(
              customers,
              customer => (
                <TableRow key={customer ? customer.id : "skeleton"}>
                  <TableCell>
                    {customer ? (
                      <span
                        onClick={onRowClick && onRowClick(customer.id)}
                        className={classes.link}
                      >
                        {customer.defaultBillingAddress.firstName +
                          " " +
                          customer.defaultBillingAddress.lastName}
                      </span>
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell>
                    {customer ? customer.email : <Skeleton />}
                  </TableCell>
                  <TableCell>
                    {customer && customer.defaultBillingAddress ? (
                      customer.defaultBillingAddress.city +
                      ", " +
                      customer.defaultBillingAddress.country.country
                    ) : (
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
    </Container>
  )
);
export default CustomerListPage;
