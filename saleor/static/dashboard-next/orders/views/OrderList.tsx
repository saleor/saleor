import { stringify as stringifyQs } from "qs";
import * as React from "react";

import { orderUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { OrderStatusFilter } from "../../types/globalTypes";
import OrderListPage from "../components/OrderListPage/OrderListPage";
import { getTabName } from "../misc";
import { TypedOrderDraftCreateMutation } from "../mutations";
import { TypedOrderListQuery } from "../queries";
import { OrderDraftCreate } from "../types/OrderDraftCreate";

export interface OrderListFilters {
  status: OrderStatusFilter;
}
export type OrderListQueryParams = Partial<
  {
    after: string;
    before: string;
  } & OrderListFilters
>;

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

          const changeFilters = (newParams: OrderListQueryParams) =>
            navigate(
              "?" +
                stringifyQs({
                  ...params,
                  ...newParams
                })
            );

          return (
            <TypedOrderDraftCreateMutation
              onCompleted={handleCreateOrderCreateSuccess}
            >
              {createOrder => {
                const paginationState = createPaginationState(
                  PAGINATE_BY,
                  params
                );
                const currentTab = getTabName(params);

                return (
                  <TypedOrderListQuery
                    variables={{
                      ...paginationState,
                      status: params.status
                    }}
                  >
                    {({ data, loading }) => (
                      <Paginator
                        pageInfo={maybe(() => data.orders.pageInfo)}
                        paginationState={paginationState}
                        queryString={params}
                      >
                        {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                          <OrderListPage
                            filtersList={[]}
                            currentTab={currentTab}
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
                            onAllProducts={() =>
                              changeFilters({
                                status: undefined
                              })
                            }
                            onToFulfill={() =>
                              changeFilters({
                                status: OrderStatusFilter.READY_TO_FULFILL
                              })
                            }
                            onToCapture={() =>
                              changeFilters({
                                status: OrderStatusFilter.READY_TO_CAPTURE
                              })
                            }
                            onCustomFilter={() => undefined}
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
