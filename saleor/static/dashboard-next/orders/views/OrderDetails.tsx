import * as React from "react";

import { orderListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { productUrl } from "../../products";
import { OrderStatus } from "../../types/globalTypes";
import OrderDetailsPage from "../components/OrderDetailsPage";
import OrderDraftPage from "../components/OrderDraftPage";
import OrderOperations from "../containers/OrderOperations";
import { OrderVariantSearchProvider } from "../containers/OrderVariantSearch";
import { TypedOrderDetailsQuery } from "../queries";
import { OrderAddNote } from "../types/OrderAddNote";
import { OrderCapture } from "../types/OrderCapture";
import { OrderCreateFulfillment } from "../types/OrderCreateFulfillment";
import { OrderDraftUpdate } from "../types/OrderDraftUpdate";
import { OrderLineAdd } from "../types/OrderLineAdd";
import { OrderLineDelete } from "../types/OrderLineDelete";
import { OrderLineUpdate } from "../types/OrderLineUpdate";
import { OrderRefund } from "../types/OrderRefund";
import { OrderShippingMethodUpdate } from "../types/OrderShippingMethodUpdate";
import { OrderUpdate } from "../types/OrderUpdate";
import { OrderFulfillmentCancel } from "../types/OrderFulfillmentCancel";
import { OrderFulfillmentUpdateTracking } from "../types/OrderFulfillmentUpdateTracking";

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
            {({ data, error }) => {
              if (error) {
                return <ErrorMessageCard message="Something went wrong" />;
              }
              const order = maybe(() => data.order);
              return (
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
                        !maybe(() => data.orderFulfillmentCreate.errors.length)
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
                    const handleOrderCancel = () => {
                      pushMessage({
                        text: i18n.t("Order successfully cancelled", {
                          context: "notification"
                        })
                      });
                    };
                    const handleOrderRelease = () => {
                      pushMessage({
                        text: i18n.t("Order payment successfully released", {
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
                      if (!maybe(() => data.draftOrderUpdate.errors.length)) {
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
                          text: i18n.t("Shipping method successfully updated", {
                            context: "notification"
                          })
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
                        !maybe(() => data.draftOrderLineDelete.errors.length)
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
                        !maybe(() => data.draftOrderLineCreate.errors.length)
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
                        !maybe(() => data.draftOrderLineUpdate.errors.length)
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
                        !maybe(() => data.orderFulfillmentCancel.errors.length)
                      ) {
                        pushMessage({
                          text: i18n.t("Fulfillment successfully cancelled", {
                            context: "notification"
                          })
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
                            data.orderFulfillmentUpdateTracking.errors.length
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
                    return (
                      <OrderOperations
                        order={id}
                        onError={undefined}
                        onOrderFulfillmentCreate={handleOrderFulfillmentCreate}
                        onNoteAdd={handleNoteAdd}
                        onOrderCancel={handleOrderCancel}
                        onOrderRelease={handleOrderRelease}
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
                      >
                        {({
                          errors,
                          orderAddNote,
                          orderCancel,
                          orderCreateFulfillment,
                          orderLineAdd,
                          orderLineDelete,
                          orderLineUpdate,
                          orderPaymentCapture,
                          orderPaymentRefund,
                          orderRelease,
                          orderShippingMethodUpdate,
                          orderUpdate,
                          orderFulfillmentCancel,
                          orderFulfillmentUpdateTracking
                        }) =>
                          maybe(() => order.status !== OrderStatus.DRAFT) ? (
                            <OrderDetailsPage
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
                                      name: `${product.name}(${variant.name})`
                                    }))
                                  )
                                  .reduce((prev, curr) => prev.concat(curr), [])
                              )}
                              onBack={() => navigate(orderListUrl)}
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
                                    lines: maybe(() => order.lines.edges, [])
                                      .map(edge => edge.node)
                                      .filter(
                                        line =>
                                          line.quantityFulfilled < line.quantity
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
                              onPaymentRelease={() =>
                                orderRelease.mutate({ id })
                              }
                              onPaymentRefund={variables =>
                                orderPaymentRefund.mutate({
                                  ...variables,
                                  id
                                })
                              }
                              onProductAdd={variables =>
                                orderLineAdd.mutate({
                                  id,
                                  input: {
                                    quantity: variables.quantity,
                                    variantId: variables.variant.value
                                  }
                                })
                              }
                              onProductClick={id => () =>
                                navigate(productUrl(id))}
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
                                    shippingMethod: variables.shippingMethod
                                  }
                                })
                              }
                              onOrderLineRemove={id =>
                                orderLineDelete.mutate({ id })
                              }
                              onOrderLineChange={id => quantity =>
                                orderLineUpdate.mutate({
                                  id,
                                  input: { quantity: parseInt(quantity, 10) }
                                })}
                            />
                          ) : (
                            <OrderDraftPage
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
                                      name: `${product.name}(${variant.name})`
                                    }))
                                  )
                                  .reduce((prev, curr) => prev.concat(curr), [])
                              )}
                              variantsLoading={searchOpts.loading}
                              fetchUsers={() => undefined}
                              onCustomerEdit={() => undefined}
                              onDraftFinalize={() => undefined}
                              onDraftRemove={() => undefined}
                              onOrderLineAdd={variables =>
                                orderLineAdd.mutate({
                                  id,
                                  input: {
                                    quantity: variables.quantity,
                                    variantId: variables.variant.value
                                  }
                                })
                              }
                              onBack={() => navigate(orderListUrl)}
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
                              onProductClick={id => () =>
                                navigate(productUrl(id))}
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
                                    shippingMethod: variables.shippingMethod
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
                              users={[]}
                            />
                          )
                        }
                      </OrderOperations>
                    );
                  }}
                </OrderVariantSearchProvider>
              );
            }}
          </TypedOrderDetailsQuery>
        )}
      </Messages>
    )}
  </Navigator>
);

export default OrderDetails;
