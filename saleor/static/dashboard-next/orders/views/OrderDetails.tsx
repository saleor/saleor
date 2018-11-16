import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { productUrl } from "../../products/urls";
import { OrderStatus } from "../../types/globalTypes";
import OrderDetailsPage from "../components/OrderDetailsPage";
import OrderDraftPage from "../components/OrderDraftPage";
import OrderOperations from "../containers/OrderOperations";
import { OrderVariantSearchProvider } from "../containers/OrderVariantSearch";
import { UserSearchProvider } from "../containers/UserSearch";
import { TypedOrderDetailsQuery } from "../queries";
import { OrderAddNote } from "../types/OrderAddNote";
import { OrderCapture } from "../types/OrderCapture";
import { OrderCreateFulfillment } from "../types/OrderCreateFulfillment";
import { OrderDraftFinalize } from "../types/OrderDraftFinalize";
import { OrderDraftUpdate } from "../types/OrderDraftUpdate";
import { OrderFulfillmentCancel } from "../types/OrderFulfillmentCancel";
import { OrderFulfillmentUpdateTracking } from "../types/OrderFulfillmentUpdateTracking";
import { OrderLineAdd } from "../types/OrderLineAdd";
import { OrderLineDelete } from "../types/OrderLineDelete";
import { OrderLineUpdate } from "../types/OrderLineUpdate";
import { OrderMarkAsPaid } from "../types/OrderMarkAsPaid";
import { OrderRefund } from "../types/OrderRefund";
import { OrderShippingMethodUpdate } from "../types/OrderShippingMethodUpdate";
import { OrderUpdate } from "../types/OrderUpdate";
import { orderListUrl } from "../urls";

interface OrderDetailsProps {
  id: string;
}

export const OrderDetails: React.StatelessComponent<OrderDetailsProps> = ({
  id
}) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => (
          <TypedOrderDetailsQuery variables={{ id }}>
            {({ data, error, loading }) => {
              if (error) {
                return <ErrorMessageCard message="Something went wrong" />;
              }
              const order = maybe(() => data.order);
              return (
                <UserSearchProvider>
                  {users => (
                    <OrderVariantSearchProvider>
                      {({ variants: { search, searchOpts } }) => {
                        const handlePaymentCapture = (data: OrderCapture) => {
                          if (!maybe(() => data.orderCapture.errors.length)) {
                            pushMessage({
                              text: i18n.t("Payment successfully captured", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t(
                                "Payment not captured: {{ errorMessage }}",
                                {
                                  context: "notification",
                                  errorMessage: data.orderCapture.errors.filter(
                                    error => error.field === "payment"
                                  )[0].message
                                }
                              )
                            });
                          }
                        };
                        const handlePaymentRefund = (data: OrderRefund) => {
                          if (!maybe(() => data.orderRefund.errors.length)) {
                            pushMessage({
                              text: i18n.t("Payment successfully refunded", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t(
                                "Payment not refunded: {{ errorMessage }}",
                                {
                                  context: "notification",
                                  errorMessage: data.orderRefund.errors.filter(
                                    error => error.field === "payment"
                                  )[0].message
                                }
                              )
                            });
                          }
                        };
                        const handleOrderFulfillmentCreate = (
                          data: OrderCreateFulfillment
                        ) => {
                          if (
                            !maybe(
                              () => data.orderFulfillmentCreate.errors.length
                            )
                          ) {
                            pushMessage({
                              text: i18n.t("Items successfully fulfilled", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not fulfill items", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleMarkAsPaid = (data: OrderMarkAsPaid) => {
                          if (
                            !maybe(() => data.orderMarkAsPaid.errors.length)
                          ) {
                            pushMessage({
                              text: i18n.t("Order marked as paid", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not mark order as paid", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleOrderCancel = () => {
                          pushMessage({
                            text: i18n.t("Order successfully cancelled", {
                              context: "notification"
                            })
                          });
                        };
                        const handleOrderDraftCancel = () => {
                          pushMessage({
                            text: i18n.t("Order successfully cancelled", {
                              context: "notification"
                            })
                          });
                          navigate(orderListUrl());
                        };
                        const handleOrderVoid = () => {
                          pushMessage({
                            text: i18n.t("Order payment successfully voided", {
                              context: "notification"
                            })
                          });
                        };
                        const handleNoteAdd = (data: OrderAddNote) => {
                          if (!maybe(() => data.orderAddNote.errors.length)) {
                            pushMessage({
                              text: i18n.t("Note successfully added", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not add note", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleUpdate = (data: OrderUpdate) => {
                          if (!maybe(() => data.orderUpdate.errors.length)) {
                            pushMessage({
                              text: i18n.t("Order successfully updated", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleDraftUpdate = (data: OrderDraftUpdate) => {
                          if (
                            !maybe(() => data.draftOrderUpdate.errors.length)
                          ) {
                            pushMessage({
                              text: i18n.t("Order successfully updated", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleShippingMethodUpdate = (
                          data: OrderShippingMethodUpdate
                        ) => {
                          if (
                            !maybe(() => data.orderUpdateShipping.errors.length)
                          ) {
                            pushMessage({
                              text: i18n.t(
                                "Shipping method successfully updated",
                                {
                                  context: "notification"
                                }
                              )
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not update shipping method", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleLineDelete = (data: OrderLineDelete) => {
                          if (
                            !maybe(
                              () => data.draftOrderLineDelete.errors.length
                            )
                          ) {
                            pushMessage({
                              text: i18n.t("Order line deleted", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not delete order line", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleLineAdd = (data: OrderLineAdd) => {
                          if (
                            !maybe(
                              () => data.draftOrderLineCreate.errors.length
                            )
                          ) {
                            pushMessage({
                              text: i18n.t("Order line added", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not create order line", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleLineUpdate = (data: OrderLineUpdate) => {
                          if (
                            !maybe(
                              () => data.draftOrderLineUpdate.errors.length
                            )
                          ) {
                            pushMessage({
                              text: i18n.t("Order line updated", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not update order line", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleFulfillmentCancel = (
                          data: OrderFulfillmentCancel
                        ) => {
                          if (
                            !maybe(
                              () => data.orderFulfillmentCancel.errors.length
                            )
                          ) {
                            pushMessage({
                              text: i18n.t(
                                "Fulfillment successfully cancelled",
                                {
                                  context: "notification"
                                }
                              )
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not cancel fulfillment", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleFulfillmentUpdate = (
                          data: OrderFulfillmentUpdateTracking
                        ) => {
                          if (
                            !maybe(
                              () =>
                                data.orderFulfillmentUpdateTracking.errors
                                  .length
                            )
                          ) {
                            pushMessage({
                              text: i18n.t("Fulfillment successfully updated", {
                                context: "notification"
                              })
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not update fulfillment", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        const handleDraftFinalize = (
                          data: OrderDraftFinalize
                        ) => {
                          if (
                            !maybe(() => data.draftOrderComplete.errors.length)
                          ) {
                            pushMessage({
                              text: i18n.t(
                                "Draft order successfully finalized",
                                {
                                  context: "notification"
                                }
                              )
                            });
                          } else {
                            pushMessage({
                              text: i18n.t("Could not finalize draft", {
                                context: "notification"
                              })
                            });
                          }
                        };
                        return (
                          <OrderOperations
                            order={id}
                            onError={undefined}
                            onOrderFulfillmentCreate={
                              handleOrderFulfillmentCreate
                            }
                            onNoteAdd={handleNoteAdd}
                            onOrderCancel={handleOrderCancel}
                            onOrderVoid={handleOrderVoid}
                            onPaymentCapture={handlePaymentCapture}
                            onPaymentRefund={handlePaymentRefund}
                            onUpdate={handleUpdate}
                            onDraftUpdate={handleDraftUpdate}
                            onShippingMethodUpdate={handleShippingMethodUpdate}
                            onOrderLineDelete={handleLineDelete}
                            onOrderLineAdd={handleLineAdd}
                            onOrderLineUpdate={handleLineUpdate}
                            onOrderFulfillmentCancel={handleFulfillmentCancel}
                            onOrderFulfillmentUpdate={handleFulfillmentUpdate}
                            onDraftFinalize={handleDraftFinalize}
                            onDraftCancel={handleOrderDraftCancel}
                            onOrderMarkAsPaid={handleMarkAsPaid}
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
                            }) =>
                              maybe(
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
                                    countries={maybe(
                                      () => data.shop.countries,
                                      []
                                    ).map(country => ({
                                      code: country.code,
                                      label: country.country
                                    }))}
                                    shippingMethods={maybe(
                                      () => data.order.availableShippingMethods,
                                      []
                                    )}
                                    onOrderCancel={variables =>
                                      orderCancel.mutate({
                                        id,
                                        ...variables
                                      })
                                    }
                                    onOrderFulfill={variables =>
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
                                              quantity:
                                                variables.lines[lineIndex]
                                            }))
                                            .filter(line => line.quantity > 0)
                                        },
                                        order: order.id
                                      })
                                    }
                                    onFulfillmentCancel={(id, variables) =>
                                      orderFulfillmentCancel.mutate({
                                        id,
                                        input: variables
                                      })
                                    }
                                    onFulfillmentTrackingNumberUpdate={(
                                      id,
                                      variables
                                    ) =>
                                      orderFulfillmentUpdateTracking.mutate({
                                        id,
                                        input: {
                                          ...variables,
                                          notifyCustomer: true
                                        }
                                      })
                                    }
                                    onPaymentCapture={variables =>
                                      orderPaymentCapture.mutate({
                                        ...variables,
                                        id
                                      })
                                    }
                                    onPaymentVoid={() =>
                                      orderVoid.mutate({ id })
                                    }
                                    onPaymentRefund={variables =>
                                      orderPaymentRefund.mutate({
                                        ...variables,
                                        id
                                      })
                                    }
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
                                    onPaymentPaid={() =>
                                      orderPaymentMarkAsPaid.mutate({ id })
                                    }
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
                              )
                            }
                          </OrderOperations>
                        );
                      }}
                    </OrderVariantSearchProvider>
                  )}
                </UserSearchProvider>
              );
            }}
          </TypedOrderDetailsQuery>
        )}
      </Messages>
    )}
  </Navigator>
);

export default OrderDetails;
