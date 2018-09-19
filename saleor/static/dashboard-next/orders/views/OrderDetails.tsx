import * as React from "react";

import { orderListUrl } from "..";
import { UserContext } from "../../auth";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import {
  OrderCaptureMutation,
  OrderCreateFulfillmentMutation,
  OrderRefundMutation
} from "../../gql-types";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { productUrl } from "../../products";
import OrderDetailsPage from "../components/OrderDetailsPage";
import OrderOperations from "../containers/OrderOperations";
import { OrderVariantSearchProvider } from "../containers/OrderVariantSearch";
import {
  TypedOrderDetailsQuery,
  TypedOrderShippingMethodsQuery
} from "../queries";
import { OrderAddNote } from "../types/OrderAddNote";
import { OrderUpdate } from "../types/OrderUpdate";

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
              const order = data && data.order;
              return (
                <UserContext.Consumer>
                  {({ user }) => (
                    <TypedOrderShippingMethodsQuery>
                      {({ data: shippingMethodsData }) => (
                        <OrderVariantSearchProvider>
                          {({ variants: { search, searchOpts } }) => {
                            const handlePaymentCapture = (
                              data: OrderCaptureMutation
                            ) => {
                              if (
                                !maybe(() => data.orderCapture.errors.length)
                              ) {
                                pushMessage({
                                  text: i18n.t("Payment succesfully captured", {
                                    context: "notification"
                                  })
                                });
                              }
                            };
                            const handlePaymentRefund = (
                              data: OrderRefundMutation
                            ) => {
                              if (
                                !maybe(() => data.orderRefund.errors.length)
                              ) {
                                pushMessage({
                                  text: i18n.t("Payment succesfully refunded", {
                                    context: "notification"
                                  })
                                });
                              }
                            };
                            const handleFulfillmentCreate = (
                              data: OrderCreateFulfillmentMutation
                            ) => {
                              if (
                                !maybe(
                                  () => data.fulfillmentCreate.errors.length
                                )
                              ) {
                                pushMessage({
                                  text: i18n.t("Items succesfully fulfilled", {
                                    context: "notification"
                                  })
                                });
                              }
                            };
                            const handleOrderCancel = () => {
                              pushMessage({
                                text: i18n.t("Order succesfully cancelled", {
                                  context: "notification"
                                })
                              });
                            };
                            const handleOrderRelease = () => {
                              pushMessage({
                                text: i18n.t(
                                  "Order payment succesfully released",
                                  {
                                    context: "notification"
                                  }
                                )
                              });
                            };
                            const handleNoteAdd = (data: OrderAddNote) => {
                              if (
                                !maybe(() => data.orderAddNote.errors.length)
                              ) {
                                pushMessage({
                                  text: i18n.t("Note succesfully added", {
                                    context: "notification"
                                  })
                                });
                              }
                            };
                            const handleUpdate = (data: OrderUpdate) => {
                              if (
                                !maybe(() => data.orderUpdate.errors.length)
                              ) {
                                pushMessage({
                                  text: i18n.t("Order succesfully updated", {
                                    context: "notification"
                                  })
                                });
                              }
                            };
                            return (
                              <OrderOperations
                                order={id}
                                onError={undefined}
                                onFulfillmentCreate={handleFulfillmentCreate}
                                onNoteAdd={handleNoteAdd}
                                onOrderCancel={handleOrderCancel}
                                onOrderRelease={handleOrderRelease}
                                onPaymentCapture={handlePaymentCapture}
                                onPaymentRefund={handlePaymentRefund}
                                onUpdate={handleUpdate}
                              >
                                {({
                                  errors,
                                  orderAddNote,
                                  orderCancel,
                                  orderCreateFulfillment,
                                  orderPaymentCapture,
                                  orderPaymentRefund,
                                  orderRelease,
                                  orderUpdate
                                }) => (
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
                                    onBack={() => navigate(orderListUrl)}
                                    order={order}
                                    countries={maybe(
                                      () => data.shop.countries,
                                      []
                                    ).map(country => ({
                                      code: country.code,
                                      label: country.country
                                    }))}
                                    shippingMethods={maybe(() =>
                                      ([] as Array<{
                                        id: string;
                                        name: string;
                                      }>).concat(
                                        ...shippingMethodsData.shippingZones.edges.map(
                                          edge =>
                                            edge.node.shippingMethods.edges.map(
                                              edge => edge.node
                                            )
                                        )
                                      )
                                    )}
                                    user={user}
                                    onOrderCancel={() =>
                                      orderCancel.mutate({ id })
                                    }
                                    onOrderFulfill={variables =>
                                      orderCreateFulfillment.mutate({
                                        input: {
                                          ...variables,
                                          lines: maybe(
                                            () => order.lines.edges,
                                            []
                                          )
                                            .map(edge => edge.node)
                                            .filter(
                                              line =>
                                                line.quantityFulfilled <
                                                line.quantity
                                            )
                                            .map((line, lineIndex) => ({
                                              orderLineId: line.id,
                                              quantity:
                                                variables.lines[lineIndex]
                                            })),
                                          order: order.id
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
                                    onProductAdd={() => undefined}
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
                                  />
                                )}
                              </OrderOperations>
                            );
                          }}
                        </OrderVariantSearchProvider>
                      )}
                    </TypedOrderShippingMethodsQuery>
                  )}
                </UserContext.Consumer>
              );
            }}
          </TypedOrderDetailsQuery>
        )}
      </Messages>
    )}
  </Navigator>
);

export default OrderDetails;
