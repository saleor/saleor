import * as React from "react";

import ErrorMessageCard from "../../../components/ErrorMessageCard";
import Navigator from "../../../components/Navigator";
import { WindowTitle } from "../../../components/WindowTitle";
import { maybe } from "../../../misc";
import { productUrl } from "../../../products/urls";
import { OrderStatus } from "../../../types/globalTypes";
import OrderDetailsPage from "../../components/OrderDetailsPage";
import OrderDraftPage from "../../components/OrderDraftPage";
import OrderOperations from "../../containers/OrderOperations";
import { OrderVariantSearchProvider } from "../../containers/OrderVariantSearch";
import { UserSearchProvider } from "../../containers/UserSearch";
import { TypedOrderDetailsQuery } from "../../queries";
import { orderListUrl } from "../../urls";
import { OrderDetailsMessages } from "./OrderDetailsMessages";

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
                          }) =>
                            maybe(() => order.status !== OrderStatus.DRAFT) ? (
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
                                  onPaymentVoid={() => orderVoid.mutate({ id })}
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
                                />
                              </>
                            )
                          }
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
