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
  TypedOrderCancelMutation,
  TypedOrderReleaseMutation
} from "../mutations";
import {
  TypedOrderDetailsQuery,
  TypedOrderShippingMethodsQuery
} from "../queries";

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
                    <TypedOrderCancelMutation variables={{ id }}>
                      {cancelOrder => (
                        <TypedOrderReleaseMutation variables={{ id }}>
                          {releasePayment => (
                            <TypedOrderShippingMethodsQuery>
                              {({ data: shippingMethodsData }) => (
                                <OrderVariantSearchProvider>
                                  {({ variants: { search, searchOpts } }) => {
                                    const handlePaymentCapture = (
                                      data: OrderCaptureMutation
                                    ) => {
                                      if (
                                        !maybe(
                                          () => data.orderCapture.errors.length
                                        )
                                      ) {
                                        pushMessage({
                                          text: i18n.t(
                                            "Payment succesfully captured",
                                            { context: "notification" }
                                          )
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
                                          text: i18n.t(
                                            "Payment succesfully refunded",
                                            { context: "notification" }
                                          )
                                        });
                                      }
                                    };
                                    const handleFulfillmentCreate = (
                                      data: OrderCreateFulfillmentMutation
                                    ) => {
                                      if (
                                        !maybe(
                                          () =>
                                            data.fulfillmentCreate.errors.length
                                        )
                                      ) {
                                        pushMessage({
                                          text: i18n.t(
                                            "Items succesfully fulfilled",
                                            { context: "notification" }
                                          )
                                        });
                                      }
                                    };
                                    return (
                                      <OrderOperations
                                        order={id}
                                        onError={undefined}
                                        onFulfillmentCreate={
                                          handleFulfillmentCreate
                                        }
                                        onPaymentCapture={handlePaymentCapture}
                                        onPaymentRefund={handlePaymentRefund}
                                      >
                                        {({
                                          orderCreateFulfillment,
                                          orderPaymentCapture,
                                          orderPaymentRefund
                                        }) => (
                                          <OrderDetailsPage
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
                                            onBack={() =>
                                              navigate(orderListUrl)
                                            }
                                            order={order}
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
                                            onOrderCancel={cancelOrder}
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
                                                        variables.lines[
                                                          lineIndex
                                                        ]
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
                                            onPaymentRelease={releasePayment}
                                            onPaymentRefund={variables =>
                                              orderPaymentRefund.mutate({
                                                ...variables,
                                                id
                                              })
                                            }
                                            onProductAdd={() => undefined}
                                            onProductClick={id => () =>
                                              navigate(productUrl(id))}
                                          />
                                        )}
                                      </OrderOperations>
                                    );
                                  }}
                                </OrderVariantSearchProvider>
                              )}
                            </TypedOrderShippingMethodsQuery>
                          )}
                        </TypedOrderReleaseMutation>
                      )}
                    </TypedOrderCancelMutation>
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
