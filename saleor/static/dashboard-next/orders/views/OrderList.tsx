import Button from "@material-ui/core/Button";
import * as React from "react";

import { createPaginationState } from "../../components/Paginator";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { OrderStatusFilter } from "../../types/globalTypes";
import OrderBulkCancelDialog from "../components/OrderBulkCancelDialog";
import OrderListPage from "../components/OrderListPage/OrderListPage";
import { getTabName } from "../misc";
import {
  TypedOrderBulkCancelMutation,
  TypedOrderDraftCreateMutation
} from "../mutations";
import { TypedOrderListQuery } from "../queries";
import { OrderBulkCancel } from "../types/OrderBulkCancel";
import { OrderDraftCreate } from "../types/OrderDraftCreate";
import {
  orderListUrl,
  OrderListUrlFilters,
  OrderListUrlQueryParams,
  orderUrl
} from "../urls";

interface OrderListProps {
  params: OrderListUrlQueryParams;
}

const PAGINATE_BY = 20;

export const OrderList: React.StatelessComponent<OrderListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );

  const closeModal = () =>
    navigate(
      orderListUrl({
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const handleCreateOrderCreateSuccess = (data: OrderDraftCreate) => {
    notify({
      text: i18n.t("Order draft succesfully created")
    });
    navigate(orderUrl(data.draftOrderCreate.order.id));
  };

  const changeFilters = (filters: OrderListUrlFilters) => {
    reset();
    navigate(
      orderListUrl({
        ...params,
        ...filters,
        after: undefined,
        before: undefined
      })
    );
  };

  const paginationState = createPaginationState(PAGINATE_BY, params);
  const currentTab = getTabName(params);

  return (
    <TypedOrderDraftCreateMutation onCompleted={handleCreateOrderCreateSuccess}>
      {createOrder => (
        <TypedOrderListQuery
          displayLoader
          variables={{
            ...paginationState,
            status: params.status
          }}
        >
          {({ data, loading, refetch }) => {
            const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
              maybe(() => data.orders.pageInfo),
              paginationState,
              params
            );

            const handleOrderBulkCancel = (data: OrderBulkCancel) => {
              if (data.orderBulkCancel.errors.length === 0) {
                notify({
                  text: i18n.t("Orders cancelled", {
                    context: "notification"
                  })
                });
                reset();
                refetch();
                closeModal();
              }
            };

            return (
              <TypedOrderBulkCancelMutation onCompleted={handleOrderBulkCancel}>
                {(orderBulkCancel, orderBulkCancelOpts) => {
                  const orderBulkCancelTransitionState = getMutationState(
                    orderBulkCancelOpts.called,
                    orderBulkCancelOpts.loading,
                    maybe(() => orderBulkCancelOpts.data.orderBulkCancel.errors)
                  );
                  const onOrderBulkCancel = (restock: boolean) =>
                    orderBulkCancel({
                      variables: {
                        ids: params.ids,
                        restock
                      }
                    });

                  return (
                    <>
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
                        onRowClick={id => () => navigate(orderUrl(id))}
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
                        isChecked={isSelected}
                        selected={listElements.length}
                        toggle={toggle}
                        toolbar={
                          <Button
                            color="primary"
                            onClick={() =>
                              navigate(
                                orderListUrl({
                                  ...params,
                                  action: "cancel",
                                  ids: listElements
                                })
                              )
                            }
                          >
                            {i18n.t("Cancel", {
                              context: "cancel orders"
                            })}
                          </Button>
                        }
                      />
                      <OrderBulkCancelDialog
                        confirmButtonState={orderBulkCancelTransitionState}
                        numberOfOrders={maybe(
                          () => params.ids.length.toString(),
                          "..."
                        )}
                        onClose={closeModal}
                        onConfirm={onOrderBulkCancel}
                        open={params.action === "cancel"}
                      />
                    </>
                  );
                }}
              </TypedOrderBulkCancelMutation>
            );
          }}
        </TypedOrderListQuery>
      )}
    </TypedOrderDraftCreateMutation>
  );
};

export default OrderList;
