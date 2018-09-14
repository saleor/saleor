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
    number: "11",
    paymentStatus: "confirmed",
    status: "fulfilled",
    total: {
      gross: {
        amount: 19.2,
        currency: "USD"
      }
    },
    userEmail: "user@example.com"
  },
  {
    client: clients[0],
    created: "2018-04-07T11:11:19+00:00",
    id: "o2",
    number: "10",
    paymentStatus: "confirmed",
    status: "unfulfilled",
    total: {
      gross: {
        amount: 28.9,
        currency: "USD"
      }
    },
    userEmail: "user@example.com"
  },
  {
    client: clients[1],
    created: "2018-04-07T10:44:44+00:00",
    id: "o3",
    number: "9",
    paymentStatus: "rejected",
    status: "fulfilled",
    total: {
      gross: {
        amount: 289.0,
        currency: "USD"
      }
    },
    userEmail: "user@example.com"
  },
  {
    client: clients[2],
    created: "2018-04-07T10:33:19+00:00",
    id: "o4",
    number: "9",
    paymentStatus: "unknown",
    status: "fulfilled",
    total: {
      gross: {
        amount: 100.05,
        currency: "USD"
      }
    },
    userEmail: "user@example.com"
  },
  {
    client: clients[3],
    created: "2018-04-07T07:39:19+00:00",
    id: "o5",
    number: "9",
    paymentStatus: "waiting",
    status: "fulfilled",
    total: {
      gross: {
        amount: 14.87,
        currency: "USD"
      }
    },
    userEmail: "user@example.com"
  },
  {
    client: clients[3],
    created: "2018-04-06T19:18:19+00:00",
    id: "o6",
    number: "8",
    paymentStatus: "rejected",
    status: "unfulfilled",
    total: {
      gross: {
        amount: 14.87,
        currency: "USD"
      }
    },
    userEmail: "user@example.com"
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
      amount: null,
      date: "2018-09-13T16:22:46.997106+00:00",
      email: null,
      emailType: null,
      id: "T3JkZXJFdmVudDoxMw==",
      message: null,
      quantity: 3,
      type: "FULFILLMENT_FULFILLED_ITEMS",
      user: {
        email: "admin@example.com"
      }
    },
    {
      amount: null,
      date: "2018-09-13T16:39:54.172431+00:00",
      email: null,
      emailType: null,
      id: "T3JkZXJFdmVudDoxNA==",
      message: null,
      quantity: null,
      type: "FULFILLMENT_FULFILLED_ITEMS",
      user: {
        email: "admin@example.com"
      }
    }
  ],
  fulfillments: [
    {
      id: "f1",
      lines: [
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
      lines: [
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
  lines: [
    {
      id: "UHJvZHVjdDox",
      price: {
        gross: {
          amount: 12.4,
          currency: "USD"
        }
      },
      productName: "Gardner, Graham and King",
      productSku: "9123021",
      quantity: 1,
      quantityFulfilled: 0,
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoy",
      price: {
        gross: {
          amount: 11.6,
          currency: "USD"
        }
      },
      productName: "Gardner and Graham",
      productSku: "9123022",
      quantity: 2,
      quantityFulfilled: 1,
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoz",
      price: {
        gross: {
          amount: 22.4,
          currency: "USD"
        }
      },
      productName: "Gardner and King",
      productSku: "9123023",
      quantity: 7,
      quantityFulfilled: 5,
      thumbnailUrl: placeholder
    },
    {
      id: "UHJvZHVjdDoa",
      price: {
        gross: {
          amount: 9.9,
          currency: "USD"
        }
      },
      productName: "Graham and King",
      productSku: "9123024",
      quantity: 3,
      quantityFulfilled: 0,
      thumbnailUrl: placeholder
    }
  ],
  number: "11",
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
  shippingPrice: {
    gross: {
      amount: 5.5,
      currency: "USD"
    }
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
  ...args
});
export const flatOrders = orders.map(order => ({
  ...order,
  orderStatus: transformOrderStatus(order.status),
  paymentStatus: transformPaymentStatus(order.paymentStatus)
}));
export const variants = [
  { id: "p1", name: "Product 1: variant 1", sku: "12345", stockQuantity: 3 },
  { id: "p2", name: "Product 1: variant 2", sku: "12346", stockQuantity: 1 },
  { id: "p3", name: "Product 2: variant 1", sku: "12355", stockQuantity: 10 },
  { id: "p4", name: "Product 3: variant 1", sku: "12445", stockQuantity: 12 },
  { id: "p5", name: "Product 3: variant 2", sku: "12545", stockQuantity: 7 },
  { id: "p6", name: "Product 5: variant 1", sku: "13345", stockQuantity: 3 },
  { id: "p7", name: "Product 5: variant 2", sku: "14345", stockQuantity: 11 }
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
