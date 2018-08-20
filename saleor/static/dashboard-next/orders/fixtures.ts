import { transformOrderStatus, transformPaymentStatus } from "./";
export const clients = [
  {
    email: "test.client1@example.com",
    id: "c1"
  },
  {
    email: "test.client2@example.com",
    id: "c2"
  },
  {
    email: "test.client3@example.com",
    id: "c3"
  },
  {
    email: "test.client4@example.com",
    id: "c4"
  }
];
export const orders = [
  {
    client: clients[0],
    created: "2018-04-07T11:18:19+00:00",
    id: "o1",
    number: 11,
    paymentStatus: "confirmed",
    price: {
      amount: 19.2,
      currency: "USD"
    },
    status: "fulfilled"
  },
  {
    client: clients[0],
    created: "2018-04-07T11:11:19+00:00",
    id: "o2",
    number: 10,
    paymentStatus: "confirmed",
    price: {
      amount: 28.9,
      currency: "USD"
    },
    status: "unfulfilled"
  },
  {
    client: clients[1],
    created: "2018-04-07T10:44:44+00:00",
    id: "o3",
    number: 9,
    paymentStatus: "rejected",
    price: {
      amount: 289.0,
      currency: "USD"
    },
    status: "fulfilled"
  },
  {
    client: clients[2],
    created: "2018-04-07T10:33:19+00:00",
    id: "o4",
    number: 9,
    paymentStatus: "unknown",
    price: {
      amount: 100.05,
      currency: "USD"
    },
    status: "fulfilled"
  },
  {
    client: clients[3],
    created: "2018-04-07T07:39:19+00:00",
    id: "o5",
    number: 9,
    paymentStatus: "waiting",
    price: {
      amount: 14.87,
      currency: "USD"
    },
    status: "fulfilled"
  },
  {
    client: clients[3],
    created: "2018-04-06T19:18:19+00:00",
    id: "o6",
    number: 8,
    paymentStatus: "rejected",
    price: {
      amount: 14.87,
      currency: "USD"
    },
    status: "unfulfilled"
  }
];
export const order = (placeholder, args?) => ({
  billingAddress: {
    city: "Keithport",
    cityArea: "",
    companyName: "",
    country: "Cyprus",
    countryArea: "",
    firstName: "Test",
    id: "a1",
    lastName: "Client",
    phone: {
      number: "",
      prefix: ""
    },
    postalCode: "95393-6818",
    streetAddress_1: "9297 Barker Extension",
    streetAddress_2: ""
  },
  client: {
    email: "test.client@example.com",
    id: "c1",
    name: "Test Client"
  },
  created: "2018-04-07T11:18:19+00:00",
  events: [
    {
      content: "Created order",
      date: "2018-04-07T11:18:19+00:00",
      id: "n1",
      type: "created",
      user: "richard.holder@example.com"
    },
    {
      content: "Received payment",
      date: "2018-04-07T11:33:19+00:00",
      id: "n2",
      params: { amount: 165.7, currency: "USD" },
      type: "payment",
      user: "richard.holder@example.com"
    },
    {
      content: "Shipped order",
      date: "2018-04-07T13:31:19+00:00",
      id: "n3",
      params: {
        shippingAddress:
          "Test Client<br />9297 Barker Extension<br />95393-6818 Keithport<br />Cyprus"
      },
      type: "shipped",
      user: "megan.finger@example.com"
    },
    {
      content:
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur arcu nisi, dignissim non placerat id, varius imperdiet nisi. Duis lobortis, massa sed feugiat ultricies, massa felis commodo dui, tempor tempus tellus ligula id arcu. Nam erat dui, fermentum sed dui a, tincidunt molestie magna.",
      date: "2018-04-08T11:18:19+00:00",
      id: "n4",
      type: "note",
      user: "megan.finger@example.com"
    }
  ],
  fulfillments: [
    {
      id: "f1",
      products: [
        {
          product: {
            id: "UHJvZHVjdDoy",
            name: "Gardner and Graham",
            thumbnailUrl: placeholder
          },
          quantity: 1
        },
        {
          product: {
            id: "UHJvZHVjdDox",
            name: "Gardner, Graham and King",
            thumbnailUrl: placeholder
          },
          quantity: 1
        }
      ],
      status: "fulfilled",
      trackingCode: "012391230412131239052"
    },
    {
      id: "f2",
      products: [
        {
          product: {
            id: "UHJvZHVjdDoy",
            name: "Gardner and Graham",
            thumbnailUrl: placeholder
          },
          quantity: 1
        }
      ],
      status: "cancelled",
      trackingCode: "012391230412131239052"
    }
  ],
  id: "o1",
  number: 11,
  payment: {
    net: {
      amount: 6,
      currency: "USD"
    },
    paid: {
      amount: 19.2,
      currency: "USD"
    },
    refunded: {
      amount: 13.2,
      currency: "USD"
    }
  },
  paymentStatus: "confirmed",
  price: {
    amount: 19.2,
    currency: "USD"
  },
  products: [
    {
      id: "UHJvZHVjdDox",
      name: "Gardner, Graham and King",
      price: {
        gross: {
          amount: 12.4,
          currency: "USD"
        }
      },
      quantity: 1,
      sku: "9123021",
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoy",
      name: "Gardner and Graham",
      price: {
        gross: {
          amount: 11.6,
          currency: "USD"
        }
      },
      quantity: 2,
      sku: "9123022",
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoz",
      name: "Gardner and King",
      price: {
        gross: {
          amount: 22.4,
          currency: "USD"
        }
      },
      quantity: 7,
      sku: "9123023",
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoa",
      name: "Graham and King",
      price: {
        gross: {
          amount: 9.9,
          currency: "USD"
        }
      },
      quantity: 3,
      sku: "9123024",
      thumbnailUrl: placeholder
    }
  ],
  shippingAddress: {
    city: "Keithport",
    cityArea: "",
    companyName: "",
    country: "Cyprus",
    countryArea: "",
    firstName: "Test",
    id: "a1",
    lastName: "Client",
    phone: {
      number: "",
      prefix: ""
    },
    postalCode: "95393-6818",
    streetAddress_1: "9297 Barker Extension",
    streetAddress_2: ""
  },
  shippingMethod: {
    id: "s1"
  },
  shippingMethodName: "DHL",
  shippingMethodPriceGross: {
    amount: 5.5,
    currency: "USD"
  },
  status: "partially fulfilled",
  subtotal: {
    amount: 160.2,
    currency: "USD"
  },
  total: {
    amount: 165.7,
    currency: "USD"
  },
  unfulfilled: [
    {
      id: "UHJvZHVjdDoy",
      name: "Gardner and Graham",
      quantity: 1,
      sku: "9123022",
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoz",
      name: "Gardner and King",
      quantity: 7,
      sku: "9123023",
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoa",
      name: "Graham and King",
      quantity: 3,
      sku: "9123024",
      thumbnailUrl: placeholder
    }
  ],
  ...args
});
export const flatOrders = orders.map(order => ({
  ...order,
  orderStatus: transformOrderStatus(order.status),
  paymentStatus: transformPaymentStatus(order.paymentStatus)
}));
export const variants = [
  { id: "p1", name: "Product 1: variant 1", sku: "12345", stockAllocated: 3 },
  { id: "p2", name: "Product 1: variant 2", sku: "12346", stockAllocated: 1 },
  { id: "p3", name: "Product 2: variant 1", sku: "12355", stockAllocated: 10 },
  { id: "p4", name: "Product 3: variant 1", sku: "12445", stockAllocated: 12 },
  { id: "p5", name: "Product 3: variant 2", sku: "12545", stockAllocated: 7 },
  { id: "p6", name: "Product 5: variant 1", sku: "13345", stockAllocated: 3 },
  { id: "p7", name: "Product 5: variant 2", sku: "14345", stockAllocated: 11 }
];
export const prefixes = ["01", "02", "41", "49"];
export const countries = [
  { code: "AF", label: "Afghanistan" },
  { code: "AX", label: "Åland Islands" },
  { code: "AL", label: "Albania" },
  { code: "DZ", label: "Algeria" },
  { code: "AS", label: "American Samoa" }
];
export const shippingMethods = [
  { id: "s1", name: "DHL", country: "whole world", price: {} },
  { id: "s2", name: "UPS", country: "Afghanistan" }
];
