import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListCustomers_customers_edges_node } from "../../types/ListCustomers";
import CustomerList from "../CustomerList/CustomerList";

export interface CustomerListPageProps extends PageListProps {
  customers: ListCustomers_customers_edges_node[];
}

const CustomerListPage: React.StatelessComponent<CustomerListPageProps> = ({
  customers,
  disabled,
  onAdd,
  ...customerListProps
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Product types")}>
      <Button
        color="secondary"
        variant="contained"
        disabled={disabled}
        onClick={onAdd}
      >
        {i18n.t("Add customer", {
          context: "button"
        })}{" "}
        <AddIcon />
      </Button>
    </PageHeader>
    <CustomerList
      customers={customers}
      disabled={disabled}
      {...customerListProps}
    />
  </Container>
);
CustomerListPage.displayName = "CustomerListPage";
export default CustomerListPage;
