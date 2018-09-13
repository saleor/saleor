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
import { Ø } from "../../misc";
import { productUrl } from "../../products";
import OrderDetailsPage from "../components/OrderDetailsPage";
import OrderOperations from "../containers/OrderOperations";
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
                              {({ data }) => {
                                const handlePaymentCapture = (
                                  data: OrderCaptureMutation
                                ) => {
                                  if (
                                    !Ø(() => data.orderCapture.errors.length)
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
                                    !Ø(() => data.orderRefund.errors.length)
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
                                    !Ø(
                                      () => data.fulfillmentCreate.errors.length
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
                                        onBack={() => navigate(orderListUrl)}
                                        order={order}
                                        shippingMethods={Ø(() =>
                                          ([] as Array<{
                                            id: string;
                                            name: string;
                                          }>).concat(
                                            ...data.shippingZones.edges.map(
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
                                              lines: Ø(
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
                                        onPaymentRelease={releasePayment}
                                        onPaymentRefund={variables =>
                                          orderPaymentRefund.mutate({
                                            ...variables,
                                            id
                                          })
                                        }
                                        onProductClick={id => () =>
                                          navigate(productUrl(id))}
                                      />
                                    )}
                                  </OrderOperations>
                                );
                              }}
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
