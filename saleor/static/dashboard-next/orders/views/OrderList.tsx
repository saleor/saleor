import * as React from "react";

import { orderListUrl, orderUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { createPaginationData, createPaginationState, maybe } from "../../misc";
import OrderListPage from "../components/OrderListPage/OrderListPage";
import { TypedOrderDraftCreateMutation } from "../mutations";
import { TypedOrderListQuery } from "../queries";
import { OrderDraftCreate } from "../types/OrderDraftCreate";

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
    {navigate => (
      <Messages>
        {pushMessage => {
          const handleCreateOrderCreateSuccess = (data: OrderDraftCreate) => {
            pushMessage({
              text: i18n.t("Order draft succesfully created")
            });
            navigate(
              orderUrl(encodeURIComponent(data.draftOrderCreate.order.id))
            );
          };
          return (
            <TypedOrderDraftCreateMutation
              onCompleted={handleCreateOrderCreateSuccess}
            >
              {createOrder => {
                const paginationState = createPaginationState(
                  PAGINATE_BY,
                  params
                );
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
                        maybe(() => data.orders.pageInfo),
                        loading
                      );
                      return (
                        <OrderListPage
                          disabled={loading}
                          orders={maybe(() =>
                            data.orders.edges.map(edge => edge.node)
                          )}
                          pageInfo={pageInfo}
                          onAdd={createOrder}
                          onNextPage={loadNextPage}
                          onPreviousPage={loadPreviousPage}
                          onRowClick={id => () =>
                            navigate(orderUrl(encodeURIComponent(id)))}
                        />
                      );
                    }}
                  </TypedOrderListQuery>
                );
              }}
            </TypedOrderDraftCreateMutation>
          );
        }}
      </Messages>
    )}
  </Navigator>
);

export default OrderList;
