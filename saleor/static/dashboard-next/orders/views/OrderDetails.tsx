import * as React from "react";

import { orderListUrl } from "..";
import { UserContext } from "../../auth";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { Ø } from "../../misc";
import { productUrl } from "../../products";
import OrderDetailsPage from "../components/OrderDetailsPage";
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
                            return (
                              <OrderDetailsPage
                                onBack={() => navigate(orderListUrl)}
                                order={order}
                                shippingMethods={Ø(() =>
                                  ([] as Array<{
                                    id: string;
                                    name: string;
                                  }>).concat(
                                    ...data.shippingZones.edges.map(edge =>
                                      edge.node.shippingMethods.edges.map(
                                        edge => edge.node
                                      )
                                    )
                                  )
                                )}
                                user={user}
                                onOrderCancel={cancelOrder}
                                onPaymentRelease={releasePayment}
                                onProductClick={id => () =>
                                  navigate(productUrl(id))}
                              />
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
  </Navigator>
);

export default OrderDetails;
