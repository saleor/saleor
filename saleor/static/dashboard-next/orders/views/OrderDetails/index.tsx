import * as React from "react";

import Navigator from "../../../components/Navigator";
import { WindowTitle } from "../../../components/WindowTitle";
import { getMutationState, maybe, transformAddressToForm } from "../../../misc";
import { productUrl } from "../../../products/urls";
import { OrderStatus } from "../../../types/globalTypes";
import OrderAddressEditDialog from "../../components/OrderAddressEditDialog";
import OrderCancelDialog from "../../components/OrderCancelDialog";
import OrderDetailsPage from "../../components/OrderDetailsPage";
import OrderDraftCancelDialog from "../../components/OrderDraftCancelDialog/OrderDraftCancelDialog";
import OrderDraftFinalizeDialog, {
  OrderDraftFinalizeWarning
} from "../../components/OrderDraftFinalizeDialog";
import OrderDraftPage from "../../components/OrderDraftPage";
import OrderFulfillmentCancelDialog from "../../components/OrderFulfillmentCancelDialog";
import OrderFulfillmentDialog from "../../components/OrderFulfillmentDialog";
import OrderFulfillmentTrackingDialog from "../../components/OrderFulfillmentTrackingDialog";
import OrderMarkAsPaidDialog from "../../components/OrderMarkAsPaidDialog/OrderMarkAsPaidDialog";
import OrderPaymentDialog from "../../components/OrderPaymentDialog";
import OrderPaymentVoidDialog from "../../components/OrderPaymentVoidDialog";
import OrderProductAddDialog from "../../components/OrderProductAddDialog";
import OrderShippingMethodEditDialog from "../../components/OrderShippingMethodEditDialog";
import OrderOperations from "../../containers/OrderOperations";
import { OrderVariantSearchProvider } from "../../containers/OrderVariantSearch";
import { UserSearchProvider } from "../../containers/UserSearch";
import { TypedOrderDetailsQuery } from "../../queries";
import { OrderDetails_order } from "../../types/OrderDetails";
import {
  orderListUrl,
  orderUrl,
  OrderUrlDialog,
  OrderUrlQueryParams
} from "../../urls";
import { OrderDetailsMessages } from "./OrderDetailsMessages";

const orderDraftFinalizeWarnings = (order: OrderDetails_order) => {
  const warnings = [] as OrderDraftFinalizeWarning[];
  if (!(order && order.shippingAddress)) {
    warnings.push("no-shipping");
  }
  if (!(order && order.billingAddress)) {
    warnings.push("no-billing");
  }
  if (!(order && (order.user || order.userEmail))) {
    warnings.push("no-user");
  }
  if (
    order &&
    order.lines &&
    order.lines.filter(line => line.isShippingRequired).length > 0 &&
    order.shippingMethod === null
  ) {
    warnings.push("no-shipping-method");
  }
  if (
    order &&
    order.lines &&
    order.lines.filter(line => line.isShippingRequired).length === 0 &&
    order.shippingMethod !== null
  ) {
    warnings.push("unnecessary-shipping-method");
  }
  return warnings;
};

interface OrderDetailsProps {
  id: string;
  params: OrderUrlQueryParams;
}

export const OrderDetails: React.StatelessComponent<OrderDetailsProps> = ({
  id,
  params
}) => (
  <Navigator>
    {navigate => (
      <TypedOrderDetailsQuery
        displayLoader
        variables={{ id }}
        require={["order"]}
      >
        {({ data, loading }) => {
          const order = maybe(() => data.order);
          const closeModal = () => navigate(orderUrl(id), true);
          const openModal = (action: OrderUrlDialog) =>
            navigate(
              orderUrl(id, {
                action
              })
            );
          return (
            <UserSearchProvider>
              {users => (
                <OrderDetailsMessages>
                  {orderMessages => (
                    <OrderOperations
                      order={id}
                      onOrderFulfillmentCreate={
                        orderMessages.handleOrderFulfillmentCreate
                      }
                      onNoteAdd={orderMessages.handleNoteAdd}
                      onOrderCancel={orderMessages.handleOrderCancel}
                      onOrderVoid={orderMessages.handleOrderVoid}
                      onPaymentCapture={orderMessages.handlePaymentCapture}
                      onPaymentRefund={orderMessages.handlePaymentRefund}
                      onUpdate={orderMessages.handleUpdate}
                      onDraftUpdate={orderMessages.handleDraftUpdate}
                      onShippingMethodUpdate={
                        orderMessages.handleShippingMethodUpdate
                      }
                      onOrderLineDelete={orderMessages.handleOrderLineDelete}
                      onOrderLineAdd={orderMessages.handleOrderLineAdd}
                      onOrderLineUpdate={orderMessages.handleOrderLineUpdate}
                      onOrderFulfillmentCancel={
                        orderMessages.handleOrderFulfillmentCancel
                      }
                      onOrderFulfillmentUpdate={
                        orderMessages.handleOrderFulfillmentUpdate
                      }
                      onDraftFinalize={orderMessages.handleDraftFinalize}
                      onDraftCancel={orderMessages.handleDraftCancel}
                      onOrderMarkAsPaid={orderMessages.handleOrderMarkAsPaid}
                    >
                      {({
                        orderAddNote,
                        orderCancel,
                        orderCreateFulfillment,
                        orderDraftUpdate,
                        orderLineAdd,
                        orderLineDelete,
                        orderLineUpdate,
                        orderPaymentCapture,
                        orderPaymentRefund,
                        orderVoid,
                        orderShippingMethodUpdate,
                        orderUpdate,
                        orderFulfillmentCancel,
                        orderFulfillmentUpdateTracking,
                        orderDraftCancel,
                        orderDraftFinalize,
                        orderPaymentMarkAsPaid
                      }) => {
                        const finalizeTransitionState = getMutationState(
                          orderDraftFinalize.opts.called,
                          orderDraftFinalize.opts.loading,
                          maybe(
                            () =>
                              orderDraftFinalize.opts.data.draftOrderComplete
                                .errors
                          )
                        );
                        return (
                          <>
                            {maybe(() => order.status !== OrderStatus.DRAFT) ? (
                              <>
                                <WindowTitle
                                  title={maybe(
                                    () => "Order #" + data.order.number
                                  )}
                                />
                                <OrderDetailsPage
                                  onNoteAdd={variables =>
                                    orderAddNote.mutate({
                                      input: variables,
                                      order: id
                                    })
                                  }
                                  onBack={() => navigate(orderListUrl())}
                                  order={order}
                                  shippingMethods={maybe(
                                    () => data.order.availableShippingMethods,
                                    []
                                  )}
                                  onOrderCancel={() => openModal("cancel")}
                                  onOrderFulfill={() => openModal("fulfill")}
                                  onFulfillmentCancel={fulfillmentId =>
                                    navigate(
                                      orderUrl(id, {
                                        action: "cancel-fulfillment",
                                        id: fulfillmentId
                                      })
                                    )
                                  }
                                  onFulfillmentTrackingNumberUpdate={fulfillmentId =>
                                    navigate(
                                      orderUrl(id, {
                                        action:'edit-fulfillment',
                                        id: fulfillmentId
                                      })
                                    )
                                  }
                                  onPaymentCapture={() => openModal("capture")}
                                  onPaymentVoid={() => openModal("void")}
                                  onPaymentRefund={() => openModal("refund")}
                                  onProductClick={id => () =>
                                    navigate(productUrl(id))}
                                  onBillingAddressEdit={() =>
                                    openModal("edit-billing-address")
                                  }
                                  onShippingAddressEdit={() =>
                                    openModal("edit-shipping-address")
                                  }
                                  onPaymentPaid={() => openModal("mark-paid")}
                                />
                                <OrderCancelDialog
                                  confirmButtonState={getMutationState(
                                    orderCancel.opts.called,
                                    orderCancel.opts.loading,
                                    maybe(
                                      () =>
                                        orderCancel.opts.data.orderCancel.errors
                                    )
                                  )}
                                  number={maybe(() => order.number)}
                                  open={params.action === "cancel"}
                                  onClose={closeModal}
                                  onSubmit={variables =>
                                    orderCancel.mutate({
                                      id,
                                      ...variables
                                    })
                                  }
                                />
                                <OrderMarkAsPaidDialog
                                  confirmButtonState={getMutationState(
                                    orderPaymentMarkAsPaid.opts.called,
                                    orderPaymentMarkAsPaid.opts.loading,
                                    maybe(
                                      () =>
                                        orderPaymentMarkAsPaid.opts.data
                                          .orderMarkAsPaid.errors
                                    )
                                  )}
                                  onClose={closeModal}
                                  onConfirm={() =>
                                    orderPaymentMarkAsPaid.mutate({
                                      id
                                    })
                                  }
                                  open={params.action === "mark-paid"}
                                />
                                <OrderPaymentVoidDialog
                                  confirmButtonState={getMutationState(
                                    orderVoid.opts.called,
                                    orderVoid.opts.loading,
                                    maybe(
                                      () => orderVoid.opts.data.orderVoid.errors
                                    )
                                  )}
                                  open={params.action === "void"}
                                  onClose={closeModal}
                                  onConfirm={() => orderVoid.mutate({ id })}
                                />
                                <OrderPaymentDialog
                                  confirmButtonState={getMutationState(
                                    orderPaymentCapture.opts.called,
                                    orderPaymentCapture.opts.loading,
                                    maybe(
                                      () =>
                                        orderPaymentCapture.opts.data
                                          .orderCapture.errors
                                    )
                                  )}
                                  initial={maybe(
                                    () => order.total.gross.amount
                                  )}
                                  open={params.action === "capture"}
                                  variant="capture"
                                  onClose={closeModal}
                                  onSubmit={variables =>
                                    orderPaymentCapture.mutate({
                                      ...variables,
                                      id
                                    })
                                  }
                                />
                                <OrderPaymentDialog
                                  confirmButtonState={getMutationState(
                                    orderPaymentRefund.opts.called,
                                    orderPaymentRefund.opts.loading,
                                    maybe(
                                      () =>
                                        orderPaymentRefund.opts.data.orderRefund
                                          .errors
                                    )
                                  )}
                                  initial={maybe(
                                    () => order.total.gross.amount
                                  )}
                                  open={params.action === "refund"}
                                  variant="refund"
                                  onClose={closeModal}
                                  onSubmit={variables =>
                                    orderPaymentRefund.mutate({
                                      ...variables,
                                      id
                                    })
                                  }
                                />
                                <OrderFulfillmentDialog
                                  confirmButtonState={getMutationState(
                                    orderCreateFulfillment.opts.called,
                                    orderCreateFulfillment.opts.loading,
                                    maybe(
                                      () =>
                                        orderCreateFulfillment.opts.data
                                          .orderFulfillmentCreate.errors
                                    )
                                  )}
                                  open={params.action === "fulfill"}
                                  lines={maybe(() => order.lines, []).filter(
                                    line =>
                                      line.quantityFulfilled < line.quantity
                                  )}
                                  onClose={closeModal}
                                  onSubmit={variables =>
                                    orderCreateFulfillment.mutate({
                                      input: {
                                        ...variables,
                                        lines: maybe(() => order.lines, [])
                                          .filter(
                                            line =>
                                              line.quantityFulfilled <
                                              line.quantity
                                          )
                                          .map((line, lineIndex) => ({
                                            orderLineId: line.id,
                                            quantity: variables.lines[lineIndex]
                                          }))
                                          .filter(line => line.quantity > 0)
                                      },
                                      order: order.id
                                    })
                                  }
                                />
                                <OrderFulfillmentCancelDialog
                                  confirmButtonState={getMutationState(
                                    orderFulfillmentCancel.opts.called,
                                    orderFulfillmentCancel.opts.loading,
                                    maybe(
                                      () =>
                                        orderFulfillmentCancel.opts.data
                                          .orderFulfillmentCancel.errors
                                    )
                                  )}
                                  open={params.action === "cancel-fulfillment"}
                                  onConfirm={variables =>
                                    orderFulfillmentCancel.mutate({
                                      id: params.id,
                                      input: variables
                                    })
                                  }
                                  onClose={closeModal}
                                />
                                <OrderFulfillmentTrackingDialog
                                  confirmButtonState={getMutationState(
                                    orderFulfillmentUpdateTracking.opts.called,
                                    orderFulfillmentUpdateTracking.opts.loading,
                                    maybe(
                                      () =>
                                        orderFulfillmentUpdateTracking.opts.data
                                          .orderFulfillmentUpdateTracking.errors
                                    )
                                  )}
                                  open={params.action === "edit-fulfillment"}
                                  trackingNumber={maybe(
                                    () =>
                                      data.order.fulfillments.find(
                                        fulfillment =>
                                          fulfillment.id === params.id
                                      ).trackingNumber
                                  )}
                                  onConfirm={variables =>
                                    orderFulfillmentUpdateTracking.mutate({
                                      id: params.id,
                                      input: {
                                        ...variables,
                                        notifyCustomer: true
                                      }
                                    })
                                  }
                                  onClose={closeModal}
                                />
                              </>
                            ) : (
                              <>
                                <WindowTitle
                                  title={maybe(
                                    () => "Draft order #" + data.order.number
                                  )}
                                />
                                <OrderDraftPage
                                  disabled={loading}
                                  onNoteAdd={variables =>
                                    orderAddNote.mutate({
                                      input: variables,
                                      order: id
                                    })
                                  }
                                  users={maybe(
                                    () =>
                                      users.searchOpts.data.customers.edges.map(
                                        edge => edge.node
                                      ),
                                    []
                                  )}
                                  fetchUsers={users.search}
                                  usersLoading={users.searchOpts.loading}
                                  onCustomerEdit={data =>
                                    orderDraftUpdate.mutate({
                                      id,
                                      input: data
                                    })
                                  }
                                  onDraftFinalize={() => openModal("finalize")}
                                  onDraftRemove={() => openModal("cancel")}
                                  onOrderLineAdd={() =>
                                    openModal("add-order-line")
                                  }
                                  onBack={() => navigate(orderListUrl())}
                                  order={order}
                                  countries={maybe(
                                    () => data.shop.countries,
                                    []
                                  ).map(country => ({
                                    code: country.code,
                                    label: country.country
                                  }))}
                                  onProductClick={id => () =>
                                    navigate(
                                      productUrl(encodeURIComponent(id))
                                    )}
                                  onBillingAddressEdit={() =>
                                    openModal("edit-billing-address")
                                  }
                                  onShippingAddressEdit={() =>
                                    openModal("edit-shipping-address")
                                  }
                                  onShippingMethodEdit={() =>
                                    openModal("edit-shipping")
                                  }
                                  onOrderLineRemove={id =>
                                    orderLineDelete.mutate({ id })
                                  }
                                  onOrderLineChange={(id, data) =>
                                    orderLineUpdate.mutate({
                                      id,
                                      input: data
                                    })
                                  }
                                  saveButtonBarState="default"
                                />
                                <OrderDraftCancelDialog
                                  confirmButtonState={getMutationState(
                                    orderDraftCancel.opts.called,
                                    orderDraftCancel.opts.loading,
                                    maybe(
                                      () =>
                                        orderDraftCancel.opts.data
                                          .draftOrderDelete.errors
                                    )
                                  )}
                                  onClose={closeModal}
                                  onConfirm={() =>
                                    orderDraftCancel.mutate({ id })
                                  }
                                  open={params.action === "cancel"}
                                  orderNumber={maybe(() => order.number)}
                                />
                                <OrderDraftFinalizeDialog
                                  confirmButtonState={finalizeTransitionState}
                                  onClose={closeModal}
                                  onConfirm={() =>
                                    orderDraftFinalize.mutate({ id })
                                  }
                                  open={params.action === "finalize"}
                                  orderNumber={maybe(() => order.number)}
                                  warnings={orderDraftFinalizeWarnings(order)}
                                />
                                <OrderShippingMethodEditDialog
                                  confirmButtonState={getMutationState(
                                    orderShippingMethodUpdate.opts.called,
                                    orderShippingMethodUpdate.opts.loading,
                                    maybe(
                                      () =>
                                        orderShippingMethodUpdate.opts.data
                                          .orderUpdateShipping.errors
                                    )
                                  )}
                                  open={params.action === "edit-shipping"}
                                  shippingMethod={maybe(
                                    () => order.shippingMethod.id,
                                    "..."
                                  )}
                                  shippingMethods={maybe(
                                    () => order.availableShippingMethods
                                  )}
                                  onClose={closeModal}
                                  onSubmit={variables =>
                                    orderShippingMethodUpdate.mutate({
                                      id,
                                      input: {
                                        shippingMethod: variables.shippingMethod
                                      }
                                    })
                                  }
                                />
                                <OrderVariantSearchProvider>
                                  {({
                                    variants: {
                                      search: variantSearch,
                                      searchOpts: variantSearchOpts
                                    }
                                  }) => {
                                    const fetchMore = () =>
                                      variantSearchOpts.loadMore(
                                        (prev, next) => {
                                          if (
                                            prev.products.pageInfo.endCursor ===
                                            next.products.pageInfo.endCursor
                                          ) {
                                            return prev;
                                          }
                                          return {
                                            ...prev,
                                            products: {
                                              ...prev.products,
                                              edges: [
                                                ...prev.products.edges,
                                                ...next.products.edges
                                              ],
                                              pageInfo: next.products.pageInfo
                                            }
                                          };
                                        },
                                        {
                                          after:
                                            variantSearchOpts.data.products
                                              .pageInfo.endCursor
                                        }
                                      );
                                    return (
                                      <OrderProductAddDialog
                                        confirmButtonState={getMutationState(
                                          orderLineAdd.opts.called,
                                          orderLineAdd.opts.loading,
                                          maybe(
                                            () =>
                                              orderLineAdd.opts.data
                                                .draftOrderLinesCreate.errors
                                          )
                                        )}
                                        loading={variantSearchOpts.loading}
                                        open={
                                          params.action === "add-order-line"
                                        }
                                        hasMore={maybe(
                                          () =>
                                            variantSearchOpts.data.products
                                              .pageInfo.hasNextPage
                                        )}
                                        products={maybe(() =>
                                          variantSearchOpts.data.products.edges.map(
                                            edge => edge.node
                                          )
                                        )}
                                        onClose={closeModal}
                                        onFetch={variantSearch}
                                        onFetchMore={fetchMore}
                                        onSubmit={formData =>
                                          orderLineAdd.mutate({
                                            id,
                                            input: formData.variants.map(
                                              variant => ({
                                                quantity: 1,
                                                variantId: variant.id
                                              })
                                            )
                                          })
                                        }
                                      />
                                    );
                                  }}
                                </OrderVariantSearchProvider>
                              </>
                            )}
                            <OrderAddressEditDialog
                              confirmButtonState={getMutationState(
                                orderUpdate.opts.called,
                                orderUpdate.opts.loading,
                                maybe(
                                  () => orderUpdate.opts.data.orderUpdate.errors
                                )
                              )}
                              address={transformAddressToForm(
                                maybe(() => order.shippingAddress)
                              )}
                              countries={maybe(
                                () => data.shop.countries,
                                []
                              ).map(country => ({
                                code: country.code,
                                label: country.country
                              }))}
                              errors={maybe(
                                () => orderUpdate.opts.data.orderUpdate.errors,
                                []
                              )}
                              open={params.action === "edit-shipping-address"}
                              variant="shipping"
                              onClose={closeModal}
                              onConfirm={variables =>
                                orderUpdate.mutate({
                                  id,
                                  input: {
                                    shippingAddress: {
                                      ...variables,
                                      country: variables.country.value
                                    }
                                  }
                                })
                              }
                            />
                            <OrderAddressEditDialog
                              confirmButtonState={getMutationState(
                                orderUpdate.opts.called,
                                orderUpdate.opts.loading,
                                maybe(
                                  () => orderUpdate.opts.data.orderUpdate.errors
                                )
                              )}
                              address={transformAddressToForm(
                                maybe(() => order.billingAddress)
                              )}
                              countries={maybe(
                                () => data.shop.countries,
                                []
                              ).map(country => ({
                                code: country.code,
                                label: country.country
                              }))}
                              errors={maybe(
                                () => orderUpdate.opts.data.orderUpdate.errors,
                                []
                              )}
                              open={params.action === "edit-billing-address"}
                              variant="billing"
                              onClose={closeModal}
                              onConfirm={variables =>
                                orderUpdate.mutate({
                                  id,
                                  input: {
                                    billingAddress: {
                                      ...variables,
                                      country: variables.country.value
                                    }
                                  }
                                })
                              }
                            />
                          </>
                        );
                      }}
                    </OrderOperations>
                  )}
                </OrderDetailsMessages>
              )}
            </UserSearchProvider>
          );
        }}
      </TypedOrderDetailsQuery>
    )}
  </Navigator>
);

export default OrderDetails;
