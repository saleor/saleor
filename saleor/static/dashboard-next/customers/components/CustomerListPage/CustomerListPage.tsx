import AddIcon from "@material-ui/icons/Add";
import Card from "material-ui/Card";
import blue from "material-ui/colors/blue";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import Table, {
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableRow
} from "material-ui/Table";
import * as React from "react";

import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface CustomerListPageProps {
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
  pageInfo?: {
    hasPreviousPage: boolean;
    hasNextPage: boolean;
  };
  onAddCustomer?();
  onNextPage?();
  onPreviousPage?();
  onRowClick?(id: string): () => void;
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
    pageInfo,
    onAddCustomer,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Container width="md">
      <PageHeader title={i18n.t("Customers")}>
        {!!onAddCustomer && (
          <IconButton onClick={onAddCustomer}>
            <AddIcon />
          </IconButton>
        )}
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
