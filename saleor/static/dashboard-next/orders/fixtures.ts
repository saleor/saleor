export const clients = [
  {
    id: "c1",
    email: "test.client-1@example.com"
  },
  {
    id: "c2",
    email: "test.client-2@example.com"
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
        created: "21 Apr 2018 16:39",
        paymentStatus: "paid",
        price: {
          localized: "19.20 USD"
        }
      }
    },
    {
      node: {
        id: "o2",
        number: 10,
        status: "unfulfilled",
        client: clients[0],
        created: "21 Apr 2018 16:31",
        paymentStatus: "paid",
        price: {
          localized: "28.90 USD"
        }
      }
    },
    {
      node: {
        id: "o2",
        number: 9,
        status: "shipped",
        client: clients[1],
        created: "21 Apr 2018 11:06",
        paymentStatus: "paid",
        price: {
          localized: "289.00 USD"
        }
      }
    }
  ]
};
