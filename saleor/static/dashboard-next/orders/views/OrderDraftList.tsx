import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import OrderDraftListPage from "../components/OrderDraftListPage";
import { TypedOrderDraftCreateMutation } from "../mutations";
import { TypedOrderDraftListQuery } from "../queries";
import { OrderDraftCreate } from "../types/OrderDraftCreate";
import { orderUrl } from "../urls";

export type OrderDraftListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface OrderDraftListProps {
  params: OrderDraftListQueryParams;
}

const PAGINATE_BY = 20;

export const OrderDraftList: React.StatelessComponent<OrderDraftListProps> = ({
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
            navigate(orderUrl(data.draftOrderCreate.order.id));
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
                  <TypedOrderDraftListQuery
                    displayLoader
                    variables={paginationState}
                  >
                    {({ data, loading }) => (
                      <Paginator
                        pageInfo={maybe(() => data.draftOrders.pageInfo)}
                        paginationState={paginationState}
                        queryString={params}
                      >
                        {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                          <OrderDraftListPage
                            disabled={loading}
                            orders={maybe(() =>
                              data.draftOrders.edges.map(edge => edge.node)
                            )}
                            pageInfo={pageInfo}
                            onAdd={createOrder}
                            onNextPage={loadNextPage}
                            onPreviousPage={loadPreviousPage}
                            onRowClick={id => () => navigate(orderUrl(id))}
                          />
                        )}
                      </Paginator>
                    )}
                  </TypedOrderDraftListQuery>
                );
              }}
            </TypedOrderDraftCreateMutation>
          );
        }}
      </Messages>
    )}
  </Navigator>
);

export default OrderDraftList;
