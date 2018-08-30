import * as React from "react";

import { orderListUrl, orderUrl } from "..";
import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState, Ø } from "../../misc";
import OrderListPage from "../components/OrderListPage/OrderListPage";
import { TypedOrderListQuery } from "../queries";

interface OrderListProps {
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 20;

export const OrderList: React.StatelessComponent<OrderListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedOrderListQuery variables={paginationState}>
          {({ data, loading }) => {
            const {
              loadNextPage,
              loadPreviousPage,
              pageInfo
            } = createPaginationData(
              navigate,
              paginationState,
              orderListUrl,
              Ø(() => data.orders.pageInfo),
              loading
            );
            return (
              <OrderListPage
                disabled={loading}
                orders={Ø(() => data.orders.edges.map(edge => edge.node))}
                pageInfo={pageInfo}
                onAdd={() => undefined}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                onRowClick={id => () => navigate(orderUrl(id))}
              />
            );
          }}
        </TypedOrderListQuery>
      );
    }}
  </Navigator>
);

export default OrderList;
