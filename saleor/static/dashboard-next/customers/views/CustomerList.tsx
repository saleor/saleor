import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState, maybe } from "../../misc";
import CustomerListPage from "../components/CustomerListPage";
import { TypedCustomerListQuery } from "../queries";
import { customerAddUrl, customerListUrl, customerUrl } from "../urls";

const PAGINATE_BY = 20;

interface CustomerListProps {
  params: {
    after?: string;
    before?: string;
  };
}

export const CustomerList: React.StatelessComponent<CustomerListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedCustomerListQuery variables={paginationState}>
          {({ data, loading }) => {
            const {
              loadNextPage,
              loadPreviousPage,
              pageInfo
            } = createPaginationData(
              navigate,
              paginationState,
              customerListUrl,
              maybe(() => data.customers.pageInfo),
              loading
            );
            return (
              <CustomerListPage
                customers={maybe(() =>
                  data.customers.edges.map(edge => edge.node)
                )}
                disabled={loading}
                pageInfo={pageInfo}
                onAdd={() => navigate(customerAddUrl)}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                onRowClick={id => () =>
                  navigate(customerUrl(encodeURIComponent(id)))}
              />
            );
          }}
        </TypedCustomerListQuery>
      );
    }}
  </Navigator>
);
export default CustomerList;
