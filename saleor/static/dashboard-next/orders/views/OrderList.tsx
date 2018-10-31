import * as React from "react";

import { orderUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import OrderListPage from "../components/OrderListPage/OrderListPage";
import { TypedOrderDraftCreateMutation } from "../mutations";
import { TypedOrderListQuery } from "../queries";
import { OrderDraftCreate } from "../types/OrderDraftCreate";

export type OrderListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface OrderListProps {
  params: OrderListQueryParams;
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
                    {({ data, loading }) => (
                      <Paginator
                        pageInfo={maybe(() => data.orders.pageInfo)}
                        paginationState={paginationState}
                        queryString={params}
                      >
                        {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                          <OrderListPage
                            filtersList={[]}
                            currentTab={0}
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
                            onAllProducts={() => undefined}
                            onToFulfill={() => undefined}
                            onToCapture={() => undefined}
                          />
                        )}
                      </Paginator>
                    )}
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
