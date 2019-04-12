import * as React from "react";

import { createPaginationState } from "../../components/Paginator";
import useNavigator from "../../hooks/useNavigator";
import usePaginator from "../../hooks/usePaginator";
import { maybe } from "../../misc";
import { Pagination } from "../../types";
import CustomerListPage from "../components/CustomerListPage";
import { TypedCustomerListQuery } from "../queries";
import { customerAddUrl, customerUrl } from "../urls";

const PAGINATE_BY = 20;

export type CustomerListQueryParams = Pagination;

interface CustomerListProps {
  params: CustomerListQueryParams;
}

export const CustomerList: React.StatelessComponent<CustomerListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const paginate = usePaginator();

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TypedCustomerListQuery displayLoader variables={paginationState}>
      {({ data, loading }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.customers.pageInfo),
          paginationState,
          params
        );

        return (
          <CustomerListPage
            customers={maybe(() => data.customers.edges.map(edge => edge.node))}
            disabled={loading}
            pageInfo={pageInfo}
            onAdd={() => navigate(customerAddUrl)}
            onNextPage={loadNextPage}
            onPreviousPage={loadPreviousPage}
            onRowClick={id => () => navigate(customerUrl(id))}
          />
        );
      }}
    </TypedCustomerListQuery>
  );
};
export default CustomerList;
