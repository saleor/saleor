import * as React from "react";
import { Route } from "react-router-dom";

import ErrorMessageCard from "../../../components/ErrorMessageCard";
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
import { orderListUrl, orderUrl } from "../../urls";
import { OrderDetailsMessages } from "./OrderDetailsMessages";
import {
  orderBillingAddressEditPath,
  orderBillingAddressEditUrl,
  orderCancelPath,
  orderCancelUrl,
  orderDraftFinalizePath,
  orderDraftFinalizeUrl,
  orderDraftLineAddPath,
  orderDraftLineAddUrl,
  orderDraftShippingMethodPath,
  orderDraftShippingMethodUrl,
  orderFulfillmentCancelPath,
  orderFulfillmentCancelUrl,
  orderFulfillmentEditTrackingPath,
  orderFulfillmentEditTrackingUrl,
  orderFulfillPath,
  orderFulfillUrl,
  orderMarkAsPaidPath,
  orderMarkAsPaidUrl,
  orderPaymentCapturePath,
  orderPaymentCaptureUrl,
  orderPaymentRefundPath,
  orderPaymentRefundUrl,
  orderPaymentVoidPath,
  orderPaymentVoidUrl,
  orderShippingAddressEditPath,
  orderShippingAddressEditUrl
} from "./urls";

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
  return warnings;
};

interface OrderDetailsProps {
  id: string;
}

export const OrderDetails: React.StatelessComponent<OrderDetailsProps> = ({
  id
}) => (
  <Navigator>
    {navigate => (
      <TypedOrderDetailsQuery displayLoader variables={{ id }}>
        {({ data, error, loading }) => {
          if (error) {
            return <ErrorMessageCard message="Something went wrong" />;
          }
          const order = maybe(() => data.order);
          const onModalClose = () => navigate(orderUrl(id), true);
          return (
            <UserSearchProvider>
              {users => (
                <OrderVariantSearchProvider>
                  {({
                    variants: {
                      search: variantSearch,
                      searchOpts: variantSearchOpts
                    }
                  }) => (
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
                          onOrderLineDelete={
                            orderMessages.handleOrderLineDelete
                          }
                          onOrderLineAdd={orderMessages.handleOrderLineAdd}
                          onOrderLineUpdate={
                            orderMessages.handleOrderLineUpdate
                          }
                          onOrderFulfillmentCancel={
                            orderMessages.handleOrderFulfillmentCancel
                          }
                          onOrderFulfillmentUpdate={
                            orderMessages.handleOrderFulfillmentUpdate
                          }
                          onDraftFinalize={orderMessages.handleDraftFinalize}
                          onDraftCancel={orderMessages.handleDraftCancel}
                          onOrderMarkAsPaid={
                            orderMessages.handleOrderMarkAsPaid
                          }
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
                                  orderDraftFinalize.opts.data
                                    .draftOrderComplete.errors
                              )
                            );
                            return (
                              <>
                                {maybe(
                                  () => order.status !== OrderStatus.DRAFT
                                ) ? (
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
                                        () =>
                                          data.order.availableShippingMethods,
                                        []
                                      )}
                                      onOrderCancel={() =>
                                        navigate(orderCancelUrl(id))
                                      }
                                      onOrderFulfill={() =>
                                        navigate(orderFulfillUrl(id))
                                      }
                                      onFulfillmentCancel={fulfillmentId =>
                                        navigate(
                                          orderFulfillmentCancelUrl(
                                            id,
                                            fulfillmentId
                                          )
                                        )
                                      }
                                      onFulfillmentTrackingNumberUpdate={fulfillmentId =>
                                        navigate(
                                          orderFulfillmentEditTrackingUrl(
                                            id,
                                            fulfillmentId
                                          )
                                        )
                                      }
                                      onPaymentCapture={() =>
                                        navigate(orderPaymentCaptureUrl(id))
                                      }
                                      onPaymentVoid={() =>
                                        navigate(orderPaymentVoidUrl(id))
                                      }
                                      onPaymentRefund={() =>
                                        navigate(orderPaymentRefundUrl(id))
                                      }
                                      onProductClick={id => () =>
                                        navigate(productUrl(id))}
                                      onBillingAddressEdit={() =>
                                        navigate(orderBillingAddressEditUrl(id))
                                      }
                                      onShippingAddressEdit={() =>
                                        navigate(
                                          orderShippingAddressEditUrl(id)
                                        )
                                      }
                                      onPaymentPaid={() =>
                                        navigate(orderMarkAsPaidUrl(id))
                                      }
                                    />
                                    <Route
                                      path={orderCancelPath(":id")}
                                      render={({ match }) => (
                                        <OrderCancelDialog
                                          confirmButtonState={getMutationState(
                                            orderCancel.opts.called,
                                            orderCancel.opts.loading,
                                            maybe(
                                              () =>
                                                orderCancel.opts.data
                                                  .orderCancel.errors
                                            )
                                          )}
                                          number={maybe(() => order.number)}
                                          open={!!match}
                                          onClose={onModalClose}
                                          onSubmit={variables =>
                                            orderCancel.mutate({
                                              id,
                                              ...variables
                                            })
                                          }
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderMarkAsPaidPath(":id")}
                                      render={({ match }) => (
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
                                          onClose={onModalClose}
                                          onConfirm={() =>
                                            orderPaymentMarkAsPaid.mutate({
                                              id
                                            })
                                          }
                                          open={!!match}
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderPaymentVoidPath(":id")}
                                      render={({ match }) => (
                                        <OrderPaymentVoidDialog
                                          confirmButtonState={getMutationState(
                                            orderVoid.opts.called,
                                            orderVoid.opts.loading,
                                            maybe(
                                              () =>
                                                orderVoid.opts.data.orderVoid
                                                  .errors
                                            )
                                          )}
                                          open={!!match}
                                          onClose={onModalClose}
                                          onConfirm={() =>
                                            orderVoid.mutate({ id })
                                          }
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderPaymentCapturePath(":id")}
                                      render={({ match }) => (
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
                                          open={!!match}
                                          variant="capture"
                                          onClose={onModalClose}
                                          onSubmit={variables =>
                                            orderPaymentCapture.mutate({
                                              ...variables,
                                              id
                                            })
                                          }
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderPaymentRefundPath(":id")}
                                      render={({ match }) => (
                                        <OrderPaymentDialog
                                          confirmButtonState={getMutationState(
                                            orderPaymentRefund.opts.called,
                                            orderPaymentRefund.opts.loading,
                                            maybe(
                                              () =>
                                                orderPaymentRefund.opts.data
                                                  .orderRefund.errors
                                            )
                                          )}
                                          initial={maybe(
                                            () => order.total.gross.amount
                                          )}
                                          open={!!match}
                                          variant="refund"
                                          onClose={onModalClose}
                                          onSubmit={variables =>
                                            orderPaymentRefund.mutate({
                                              ...variables,
                                              id
                                            })
                                          }
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderFulfillPath(":id")}
                                      render={({ match }) => (
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
                                          open={!!match}
                                          lines={maybe(
                                            () => order.lines,
                                            []
                                          ).filter(
                                            line =>
                                              line.quantityFulfilled <
                                              line.quantity
                                          )}
                                          onClose={onModalClose}
                                          onSubmit={variables =>
                                            orderCreateFulfillment.mutate({
                                              input: {
                                                ...variables,
                                                lines: maybe(
                                                  () => order.lines,
                                                  []
                                                )
                                                  .filter(
                                                    line =>
                                                      line.quantityFulfilled <
                                                      line.quantity
                                                  )
                                                  .map((line, lineIndex) => ({
                                                    orderLineId: line.id,
                                                    quantity:
                                                      variables.lines[lineIndex]
                                                  }))
                                                  .filter(
                                                    line => line.quantity > 0
                                                  )
                                              },
                                              order: order.id
                                            })
                                          }
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderFulfillmentCancelPath(
                                        ":orderId",
                                        ":fulfillmentId"
                                      )}
                                      render={({ match }) => (
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
                                          open={!!match}
                                          onConfirm={variables =>
                                            orderFulfillmentCancel.mutate({
                                              id: decodeURIComponent(
                                                match.params.fulfillmentId
                                              ),
                                              input: variables
                                            })
                                          }
                                          onClose={onModalClose}
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderFulfillmentEditTrackingPath(
                                        ":orderId",
                                        ":fulfillmentId"
                                      )}
                                      render={({ match }) => (
                                        <OrderFulfillmentTrackingDialog
                                          confirmButtonState={getMutationState(
                                            orderFulfillmentUpdateTracking.opts
                                              .called,
                                            orderFulfillmentUpdateTracking.opts
                                              .loading,
                                            maybe(
                                              () =>
                                                orderFulfillmentUpdateTracking
                                                  .opts.data
                                                  .orderFulfillmentUpdateTracking
                                                  .errors
                                            )
                                          )}
                                          open={!!match}
                                          trackingNumber={maybe(
                                            () =>
                                              data.order.fulfillments.find(
                                                fulfillment =>
                                                  fulfillment.id ===
                                                  decodeURIComponent(
                                                    match.params.fulfillmentId
                                                  )
                                              ).trackingNumber
                                          )}
                                          onConfirm={variables =>
                                            orderFulfillmentUpdateTracking.mutate(
                                              {
                                                id: decodeURIComponent(
                                                  match.params.fulfillmentId
                                                ),
                                                input: {
                                                  ...variables,
                                                  notifyCustomer: true
                                                }
                                              }
                                            )
                                          }
                                          onClose={onModalClose}
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderCancelPath(":id")}
                                      render={({ match }) => (
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
                                          onClose={onModalClose}
                                          onConfirm={() =>
                                            orderDraftCancel.mutate({ id })
                                          }
                                          open={!!match}
                                          orderNumber={maybe(
                                            () => order.number
                                          )}
                                        />
                                      )}
                                    />
                                  </>
                                ) : (
                                  <>
                                    <WindowTitle
                                      title={maybe(
                                        () =>
                                          "Draft order #" + data.order.number
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
                                      fetchVariants={variantSearch}
                                      variants={maybe(() =>
                                        variantSearchOpts.data.products.edges
                                          .map(edge => edge.node)
                                          .map(product =>
                                            product.variants.map(variant => ({
                                              ...variant,
                                              name: `${product.name}(${
                                                variant.name
                                              })`
                                            }))
                                          )
                                          .reduce(
                                            (prev, curr) => prev.concat(curr),
                                            []
                                          )
                                      )}
                                      users={maybe(
                                        () =>
                                          users.searchOpts.data.customers.edges.map(
                                            edge => edge.node
                                          ),
                                        []
                                      )}
                                      variantsLoading={
                                        variantSearchOpts.loading
                                      }
                                      fetchUsers={users.search}
                                      usersLoading={users.searchOpts.loading}
                                      onCustomerEdit={data =>
                                        orderDraftUpdate.mutate({
                                          id,
                                          input: data
                                        })
                                      }
                                      onDraftFinalize={() =>
                                        navigate(
                                          orderDraftFinalizeUrl(id),
                                          true
                                        )
                                      }
                                      onDraftRemove={() =>
                                        navigate(orderCancelUrl(id))
                                      }
                                      onOrderLineAdd={() =>
                                        navigate(orderDraftLineAddUrl(id))
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
                                        navigate(orderBillingAddressEditUrl(id))
                                      }
                                      onShippingAddressEdit={() =>
                                        navigate(
                                          orderShippingAddressEditUrl(id)
                                        )
                                      }
                                      onShippingMethodEdit={() =>
                                        navigate(
                                          orderDraftShippingMethodUrl(id)
                                        )
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
                                    <Route
                                      path={orderCancelPath(":id")}
                                      render={({ match }) => (
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
                                          onClose={onModalClose}
                                          onConfirm={() =>
                                            orderDraftCancel.mutate({ id })
                                          }
                                          open={!!match}
                                          orderNumber={maybe(
                                            () => order.number
                                          )}
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderDraftFinalizePath(":id")}
                                      render={({ match }) => (
                                        <OrderDraftFinalizeDialog
                                          confirmButtonState={
                                            finalizeTransitionState
                                          }
                                          onClose={onModalClose}
                                          onConfirm={() =>
                                            orderDraftFinalize.mutate({ id })
                                          }
                                          open={!!match}
                                          orderNumber={maybe(
                                            () => order.number
                                          )}
                                          warnings={orderDraftFinalizeWarnings(
                                            order
                                          )}
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderDraftShippingMethodPath(":id")}
                                      render={({ match }) => (
                                        <OrderShippingMethodEditDialog
                                          confirmButtonState={getMutationState(
                                            orderShippingMethodUpdate.opts
                                              .called,
                                            orderShippingMethodUpdate.opts
                                              .loading,
                                            maybe(
                                              () =>
                                                orderShippingMethodUpdate.opts
                                                  .data.orderUpdateShipping
                                                  .errors
                                            )
                                          )}
                                          open={!!match}
                                          shippingMethod={maybe(
                                            () => order.shippingMethod.id,
                                            ""
                                          )}
                                          shippingMethods={maybe(
                                            () => order.availableShippingMethods
                                          )}
                                          onClose={onModalClose}
                                          onSubmit={variables =>
                                            orderShippingMethodUpdate.mutate({
                                              id,
                                              input: {
                                                shippingMethod:
                                                  variables.shippingMethod
                                              }
                                            })
                                          }
                                        />
                                      )}
                                    />
                                    <Route
                                      path={orderDraftLineAddPath(":id")}
                                      render={({ match }) => (
                                        <OrderProductAddDialog
                                          confirmButtonState={getMutationState(
                                            orderLineAdd.opts.called,
                                            orderLineAdd.opts.loading,
                                            maybe(
                                              () =>
                                                orderLineAdd.opts.data
                                                  .draftOrderLineCreate.errors
                                            )
                                          )}
                                          loading={variantSearchOpts.loading}
                                          open={!!match}
                                          variants={maybe(() =>
                                            variantSearchOpts.data.products.edges
                                              .map(edge => edge.node)
                                              .map(product =>
                                                product.variants.map(
                                                  variant => ({
                                                    ...variant,
                                                    name: `${product.name}(${
                                                      variant.name
                                                    })`
                                                  })
                                                )
                                              )
                                              .reduce(
                                                (prev, curr) =>
                                                  prev.concat(curr),
                                                []
                                              )
                                          )}
                                          fetchVariants={variantSearch}
                                          onClose={onModalClose}
                                          onSubmit={variables =>
                                            orderLineAdd.mutate({
                                              id,
                                              input: {
                                                quantity: variables.quantity,
                                                variantId:
                                                  variables.variant.value
                                              }
                                            })
                                          }
                                        />
                                      )}
                                    />
                                  </>
                                )}
                                <Route
                                  path={orderShippingAddressEditPath(":id")}
                                  render={({ match }) => (
                                    <OrderAddressEditDialog
                                      confirmButtonState={getMutationState(
                                        orderUpdate.opts.called,
                                        orderUpdate.opts.loading,
                                        maybe(
                                          () =>
                                            orderUpdate.opts.data.orderUpdate
                                              .errors
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
                                        () =>
                                          orderUpdate.opts.data.orderUpdate
                                            .errors,
                                        []
                                      )}
                                      open={!!match}
                                      variant="shipping"
                                      onClose={onModalClose}
                                      onConfirm={variables =>
                                        orderUpdate.mutate({
                                          id,
                                          input: {
                                            shippingAddress: variables
                                          }
                                        })
                                      }
                                    />
                                  )}
                                />
                                <Route
                                  path={orderBillingAddressEditPath(":id")}
                                  render={({ match }) => (
                                    <OrderAddressEditDialog
                                      confirmButtonState={getMutationState(
                                        orderUpdate.opts.called,
                                        orderUpdate.opts.loading,
                                        maybe(
                                          () =>
                                            orderUpdate.opts.data.orderUpdate
                                              .errors
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
                                        () =>
                                          orderUpdate.opts.data.orderUpdate
                                            .errors,
                                        []
                                      )}
                                      open={!!match}
                                      variant="billing"
                                      onClose={onModalClose}
                                      onConfirm={variables =>
                                        orderUpdate.mutate({
                                          id,
                                          input: {
                                            billingAddress: variables
                                          }
                                        })
                                      }
                                    />
                                  )}
                                />
                              </>
                            );
                          }}
                        </OrderOperations>
                      )}
                    </OrderDetailsMessages>
                  )}
                </OrderVariantSearchProvider>
              )}
            </UserSearchProvider>
          );
        }}
      </TypedOrderDetailsQuery>
    )}
  </Navigator>
);

export default OrderDetails;
