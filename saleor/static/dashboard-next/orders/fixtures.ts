import { transformOrderStatus, transformPaymentStatus } from "./";
export const clients = [
  {
    id: "c1",
    email: "test.client1@example.com"
  },
  {
    id: "c2",
    email: "test.client2@example.com"
  },
  {
    id: "c3",
    email: "test.client3@example.com"
  },
  {
    id: "c4",
    email: "test.client4@example.com"
  }
];
export const orders = {
  edges: [
    {
      node: {
        id: "o1",
        number: 11,
        status: "fulfilled",
        client: clients[0],
        created: "2018-04-07T11:18:19+00:00",
        paymentStatus: "confirmed",
        price: {
          amount: 19.2,
          currency: "USD"
        }
      }
    },
    {
      node: {
        id: "o2",
        number: 10,
        status: "unfulfilled",
        client: clients[0],
        created: "2018-04-07T11:11:19+00:00",
        paymentStatus: "confirmed",
        price: {
          amount: 28.9,
          currency: "USD"
        }
      }
    },
    {
      node: {
        id: "o2",
        number: 9,
        status: "shipped",
        client: clients[1],
        created: "2018-04-07T10:44:44+00:00",
        paymentStatus: "rejected",
        price: {
          amount: 289.0,
          currency: "USD"
        }
      }
    },
    {
      node: {
        id: "o3",
        number: 9,
        status: "shipped",
        client: clients[2],
        created: "2018-04-07T10:33:19+00:00",
        paymentStatus: "unknown",
        price: {
          amount: 100.05,
          currency: "USD"
        }
      }
    },
    {
      node: {
        id: "o2",
        number: 9,
        status: "shipped",
        client: clients[3],
        created: "2018-04-07T07:39:19+00:00",
        paymentStatus: "waiting",
        price: {
          amount: 14.87,
          currency: "USD"
        }
      }
    }
  ]
};
export const flatOrders = orders.edges.map(edge => ({
  ...edge.node,
  orderStatus: transformOrderStatus(edge.node.status),
  paymentStatus: transformPaymentStatus(edge.node.paymentStatus)
}));
