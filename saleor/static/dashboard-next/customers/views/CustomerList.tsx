import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { maybe } from "../../misc";
import CustomerListPage from "../components/CustomerListPage";
import { TypedCustomerListQuery } from "../queries";
import { customerAddUrl, customerUrl } from "../urls";

const PAGINATE_BY = 20;

export type CustomerListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface CustomerListProps {
  params: CustomerListQueryParams;
}

export const CustomerList: React.StatelessComponent<CustomerListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedCustomerListQuery displayLoader variables={paginationState}>
          {({ data, loading }) => (
            <Paginator
              pageInfo={maybe(() => data.customers.pageInfo)}
              paginationState={paginationState}
              queryString={params}
            >
              {({ loadNextPage, loadPreviousPage, pageInfo }) => (
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
              )}
            </Paginator>
          )}
        </TypedCustomerListQuery>
      );
    }}
  </Navigator>
);
export default CustomerList;
