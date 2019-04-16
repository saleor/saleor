import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { createPaginationState } from "../../components/Paginator";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import OrderDraftListPage from "../components/OrderDraftListPage";
import {
  TypedOrderDraftBulkCancelMutation,
  TypedOrderDraftCreateMutation
} from "../mutations";
import { TypedOrderDraftListQuery } from "../queries";
import { OrderDraftBulkCancel } from "../types/OrderDraftBulkCancel";
import { OrderDraftCreate } from "../types/OrderDraftCreate";
import {
  orderDraftListUrl,
  OrderDraftListUrlQueryParams,
  orderUrl
} from "../urls";

interface OrderDraftListProps {
  params: OrderDraftListUrlQueryParams;
}

const PAGINATE_BY = 20;

export const OrderDraftList: React.StatelessComponent<OrderDraftListProps> = ({
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
      orderDraftListUrl({
        ...params,
        action: undefined,
        ids: undefined
      })
    );

  const handleCreateOrderCreateSuccess = (data: OrderDraftCreate) => {
    notify({
      text: i18n.t("Order draft succesfully created")
    });
    navigate(orderUrl(data.draftOrderCreate.order.id));
  };

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TypedOrderDraftCreateMutation onCompleted={handleCreateOrderCreateSuccess}>
      {createOrder => (
        <TypedOrderDraftListQuery displayLoader variables={paginationState}>
          {({ data, loading, refetch }) => {
            const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
              maybe(() => data.draftOrders.pageInfo),
              paginationState,
              params
            );

            const handleOrderDraftBulkCancel = (data: OrderDraftBulkCancel) => {
              if (data.draftOrderBulkDelete.errors.length === 0) {
                notify({
                  text: i18n.t("Removed draft orders")
                });
                refetch();
                reset();
                closeModal();
              }
            };

            return (
              <TypedOrderDraftBulkCancelMutation
                onCompleted={handleOrderDraftBulkCancel}
              >
                {(orderDraftBulkDelete, orderDraftBulkDeleteOpts) => {
                  const bulkRemoveTransitionState = getMutationState(
                    orderDraftBulkDeleteOpts.called,
                    orderDraftBulkDeleteOpts.loading,
                    maybe(
                      () =>
                        orderDraftBulkDeleteOpts.data.draftOrderBulkDelete
                          .errors
                    )
                  );
                  const onOrderDraftBulkDelete = () =>
                    orderDraftBulkDelete({
                      variables: {
                        ids: params.ids
                      }
                    });

                  return (
                    <>
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
                        isChecked={isSelected}
                        selected={listElements.length}
                        toggle={toggle}
                        toolbar={
                          <IconButton
                            color="primary"
                            onClick={() =>
                              navigate(
                                orderDraftListUrl({
                                  action: "remove",
                                  ids: listElements
                                })
                              )
                            }
                          >
                            <DeleteIcon />
                          </IconButton>
                        }
                      />
                      <ActionDialog
                        confirmButtonState={bulkRemoveTransitionState}
                        onClose={closeModal}
                        onConfirm={onOrderDraftBulkDelete}
                        open={params.action === "remove"}
                        title={i18n.t("Remove Order Drafts")}
                        variant="delete"
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to remove <strong>{{ number }}</strong> order drafts?",
                              {
                                number: maybe(
                                  () => params.ids.length.toString(),
                                  "..."
                                )
                              }
                            )
                          }}
                        />
                      </ActionDialog>
                    </>
                  );
                }}
              </TypedOrderDraftBulkCancelMutation>
            );
          }}
        </TypedOrderDraftListQuery>
      )}
    </TypedOrderDraftCreateMutation>
  );
};

export default OrderDraftList;
