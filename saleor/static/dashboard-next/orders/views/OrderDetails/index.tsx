import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../../components/ActionDialog";
import ErrorMessageCard from "../../../components/ErrorMessageCard";
import Navigator from "../../../components/Navigator";
import { WindowTitle } from "../../../components/WindowTitle";
import i18n from "../../../i18n";
import { maybe, transformAddressToForm } from "../../../misc";
import { productUrl } from "../../../products/urls";
import { OrderStatus } from "../../../types/globalTypes";
import OrderAddressEditDialog from "../../components/OrderAddressEditDialog";
import OrderCancelDialog from "../../components/OrderCancelDialog";
import OrderDetailsPage from "../../components/OrderDetailsPage";
import OrderDraftPage from "../../components/OrderDraftPage";
import OrderFulfillmentCancelDialog from "../../components/OrderFulfillmentCancelDialog";
import OrderFulfillmentDialog from "../../components/OrderFulfillmentDialog";
import OrderFulfillmentTrackingDialog from "../../components/OrderFulfillmentTrackingDialog";
import OrderMarkAsPaidDialog from "../../components/OrderMarkAsPaidDialog/OrderMarkAsPaidDialog";
import OrderPaymentDialog from "../../components/OrderPaymentDialog";
import OrderPaymentVoidDialog from "../../components/OrderPaymentVoidDialog";
import OrderOperations from "../../containers/OrderOperations";
import { OrderVariantSearchProvider } from "../../containers/OrderVariantSearch";
import { UserSearchProvider } from "../../containers/UserSearch";
import { TypedOrderDetailsQuery } from "../../queries";
import { orderListUrl, orderUrl } from "../../urls";
import { OrderDetailsMessages } from "./OrderDetailsMessages";
import {
  orderBillingAddressEditUrl,
  orderCancelUrl,
  orderFulfillmentCancelUrl,
  orderFulfillmentEditTrackingUrl,
  orderFulfillUrl,
  orderMarkAsPaidUrl,
  orderPaymentCaptureUrl,
  orderPaymentRefundUrl,
  orderPaymentVoidUrl,
  orderShippingAddressEditUrl
} from "./urls";

interface OrderDetailsProps {
  id: string;
}

export const OrderDetails: React.StatelessComponent<OrderDetailsProps> = ({
  id
}) => (
  <Navigator>
    {navigate => (
      <TypedOrderDetailsQuery variables={{ id }}>
        {({ data, error, loading }) => {
          if (error) {
            return <ErrorMessageCard message="Something went wrong" />;
          }
          const order = maybe(() => data.order);
          const encodedId = encodeURIComponent(id);
          const onModalClose = () => navigate(orderUrl(encodedId), true);
          return (
            <UserSearchProvider>
              {users => (
                <OrderVariantSearchProvider>
                  {({ variants: { search, searchOpts } }) => (
                    <OrderDetailsMessages>
                      {orderMessages => (
                        <OrderOperations
                          order={id}
                          onError={undefined}
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
                            errors,
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
                          }) => (
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
                                    errors={errors}
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
                                    onOrderCancel={() =>
                                      navigate(orderCancelUrl(encodedId))
                                    }
                                    onOrderFulfill={() =>
                                      navigate(orderFulfillUrl(encodedId))
                                    }
                                    onFulfillmentCancel={fulfillmentId =>
                                      navigate(
                                        orderFulfillmentCancelUrl(
                                          encodedId,
                                          encodeURIComponent(fulfillmentId)
                                        )
                                      )
                                    }
                                    onFulfillmentTrackingNumberUpdate={fulfillmentId =>
                                      navigate(
                                        orderFulfillmentEditTrackingUrl(
                                          encodedId,
                                          encodeURIComponent(fulfillmentId)
                                        )
                                      )
                                    }
                                    onPaymentCapture={() =>
                                      navigate(
                                        orderPaymentCaptureUrl(encodedId)
                                      )
                                    }
                                    onPaymentVoid={() =>
                                      navigate(orderPaymentVoidUrl(encodedId))
                                    }
                                    onPaymentRefund={() =>
                                      navigate(orderPaymentRefundUrl(encodedId))
                                    }
                                    onProductClick={id => () =>
                                      navigate(
                                        productUrl(encodeURIComponent(id))
                                      )}
                                    onBillingAddressEdit={() =>
                                      navigate(
                                        orderBillingAddressEditUrl(encodedId)
                                      )
                                    }
                                    onShippingAddressEdit={() =>
                                      navigate(
                                        orderShippingAddressEditUrl(encodedId)
                                      )
                                    }
                                    onPaymentPaid={() =>
                                      navigate(orderMarkAsPaidUrl(encodedId))
                                    }
                                  />
                                  <Route
                                    path={orderCancelUrl(":id")}
                                    render={({ match }) => (
                                      <OrderCancelDialog
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
                                    path={orderMarkAsPaidUrl(":id")}
                                    render={({ match }) => (
                                      <OrderMarkAsPaidDialog
                                        onClose={onModalClose}
                                        onConfirm={() =>
                                          orderPaymentMarkAsPaid.mutate({ id })
                                        }
                                        open={!!match}
                                      />
                                    )}
                                  />
                                  <Route
                                    path={orderPaymentVoidUrl(":id")}
                                    render={({ match }) => (
                                      <OrderPaymentVoidDialog
                                        open={!!match}
                                        onClose={onModalClose}
                                        onConfirm={() =>
                                          orderVoid.mutate({ id })
                                        }
                                      />
                                    )}
                                  />
                                  <Route
                                    path={orderPaymentCaptureUrl(":id")}
                                    render={({ match }) => (
                                      <OrderPaymentDialog
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
                                    path={orderPaymentRefundUrl(":id")}
                                    render={({ match }) => (
                                      <OrderPaymentDialog
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
                                    path={orderFulfillUrl(":id")}
                                    render={({ match }) => (
                                      <OrderFulfillmentDialog
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
                                    path={orderFulfillmentCancelUrl(
                                      ":orderId",
                                      ":fulfillmentId"
                                    )}
                                    render={({ match }) => (
                                      <OrderFulfillmentCancelDialog
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
                                    path={orderFulfillmentEditTrackingUrl(
                                      ":orderId",
                                      ":fulfillmentId"
                                    )}
                                    render={({ match }) => (
                                      <OrderFulfillmentTrackingDialog
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
                                    path={orderShippingAddressEditUrl(":id")}
                                    render={({ match }) => (
                                      <OrderAddressEditDialog
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
                                        errors={errors}
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
                                    path={orderBillingAddressEditUrl(":id")}
                                    render={({ match }) => (
                                      <OrderAddressEditDialog
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
                                        errors={errors}
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
                              ) : (
                                <>
                                  <WindowTitle
                                    title={maybe(
                                      () => "Draft order #" + data.order.number
                                    )}
                                  />
                                  <OrderDraftPage
                                    disabled={loading}
                                    errors={errors}
                                    onNoteAdd={variables =>
                                      orderAddNote.mutate({
                                        input: variables,
                                        order: id
                                      })
                                    }
                                    fetchVariants={search}
                                    variants={maybe(() =>
                                      searchOpts.data.products.edges
                                        .map(edge => edge.node)
                                        .map(product => ({
                                          ...product,
                                          variants: product.variants.edges.map(
                                            edge => edge.node
                                          )
                                        }))
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
                                    variantsLoading={searchOpts.loading}
                                    fetchUsers={users.search}
                                    usersLoading={users.searchOpts.loading}
                                    onCustomerEdit={data =>
                                      orderDraftUpdate.mutate({
                                        id,
                                        input: data
                                      })
                                    }
                                    onDraftFinalize={() =>
                                      orderDraftFinalize.mutate({ id })
                                    }
                                    onDraftRemove={() =>
                                      orderDraftCancel.mutate({ id })
                                    }
                                    onOrderLineAdd={variables =>
                                      orderLineAdd.mutate({
                                        id,
                                        input: {
                                          quantity: variables.quantity,
                                          variantId: variables.variant.value
                                        }
                                      })
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
                                    onBillingAddressEdit={variables =>
                                      orderUpdate.mutate({
                                        id,
                                        input: {
                                          billingAddress: variables
                                        }
                                      })
                                    }
                                    onShippingAddressEdit={variables =>
                                      orderUpdate.mutate({
                                        id,
                                        input: {
                                          shippingAddress: variables
                                        }
                                      })
                                    }
                                    onShippingMethodEdit={variables =>
                                      orderShippingMethodUpdate.mutate({
                                        id,
                                        input: {
                                          shippingMethod:
                                            variables.shippingMethod
                                        }
                                      })
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
                                  />
                                </>
                              )}
                            </>
                          )}
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
