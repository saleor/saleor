import { OrderStatus, PaymentStatusEnum } from "../types/globalTypes";
import { transformOrderStatus, transformPaymentStatus } from "./";
import { OrderList_orders_edges_node } from "./types/OrderList";
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
export const orders: OrderList_orders_edges_node[] = [
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "East Aaronville",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "BE",
        country: "Belgia"
      },
      countryArea: "",
      firstName: "Laura",
      id: "QWRkcmVzczo5",
      lastName: "Stone 1 2",
      phone: "",
      postalCode: "88741",
      streetAddress1: "3678 John Course",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:30.376876+00:00",
    id: "T3JkZXI6MjA=",
    number: "20",
    paymentStatus: PaymentStatusEnum.CONFIRMED,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 305.17,
        currency: "USD"
      }
    },
    userEmail: "laura.stone@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Port Danielshire",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "SE",
        country: "Szwecja"
      },
      countryArea: "",
      firstName: "Elizabeth",
      id: "QWRkcmVzczoy",
      lastName: "Vaughn",
      phone: "",
      postalCode: "52203",
      streetAddress1: "419 Ruiz Orchard Apt. 199",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:30.124154+00:00",
    id: "T3JkZXI6MTk=",
    number: "19",
    paymentStatus: PaymentStatusEnum.CONFIRMED,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 1215.89,
        currency: "USD"
      }
    },
    userEmail: "elizabeth.vaughn@example.com"
  },
  {
    __typename: "Order",
    billingAddress: null,
    created: "2018-09-11T09:37:30.019749+00:00",
    id: "T3JkZXI6MTg=",
    number: "18",
    paymentStatus: PaymentStatusEnum.PREAUTH,
    status: OrderStatus.DRAFT,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 321.71,
        currency: "USD"
      }
    },
    userEmail: "david.lawson@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "South Rodneymouth",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "GR",
        country: "Grecja"
      },
      countryArea: "",
      firstName: "Aaron",
      id: "QWRkcmVzczoyOA==",
      lastName: "Randall",
      phone: "",
      postalCode: "30356",
      streetAddress1: "326 Palmer Rapids Apt. 717",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:29.864391+00:00",
    id: "T3JkZXI6MTc=",
    number: "17",
    paymentStatus: PaymentStatusEnum.PREAUTH,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 271.95,
        currency: "USD"
      }
    },
    userEmail: "aaron.randall@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Jorgeview",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "UG",
        country: "Uganda"
      },
      countryArea: "",
      firstName: "Laura",
      id: "QWRkcmVzczoxNA==",
      lastName: "Jensen",
      phone: "",
      postalCode: "77693",
      streetAddress1: "01504 Olson Springs Suite 920",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:29.610339+00:00",
    id: "T3JkZXI6MTY=",
    number: "16",
    paymentStatus: PaymentStatusEnum.PREAUTH,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 335.84,
        currency: "USD"
      }
    },
    userEmail: "laura.jensen@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "East Lauriestad",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "PW",
        country: "Palau"
      },
      countryArea: "",
      firstName: "Jenna",
      id: "QWRkcmVzczoyNw==",
      lastName: "Villa",
      phone: "",
      postalCode: "65613",
      streetAddress1: "2031 Mcdonald Mill",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:29.336209+00:00",
    id: "T3JkZXI6MTU=",
    number: "15",
    paymentStatus: PaymentStatusEnum.REJECTED,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 1042.15,
        currency: "USD"
      }
    },
    userEmail: "jenna.villa@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Kaneton",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "VA",
        country: "Watykan"
      },
      countryArea: "",
      firstName: "Wesley",
      id: "QWRkcmVzczo4",
      lastName: "Davis",
      phone: "",
      postalCode: "66203",
      streetAddress1: "667 Joseph Lights",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:29.103651+00:00",
    id: "T3JkZXI6MTQ=",
    number: "14",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 213.69,
        currency: "USD"
      }
    },
    userEmail: "wesley.davis@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "New Morganshire",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "NL",
        country: "Holandia"
      },
      countryArea: "",
      firstName: "Anthony",
      id: "QWRkcmVzczo3",
      lastName: "Gonzalez",
      phone: "",
      postalCode: "78701",
      streetAddress1: "402 Mason Viaduct Suite 592",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:28.921956+00:00",
    id: "T3JkZXI6MTM=",
    number: "13",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 367.03,
        currency: "USD"
      }
    },
    userEmail: "anthony.gonzalez@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Adamsport",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "TN",
        country: "Tunezja"
      },
      countryArea: "",
      firstName: "Denise",
      id: "QWRkcmVzczoyNg==",
      lastName: "Freeman",
      phone: "",
      postalCode: "27744",
      streetAddress1: "8376 Linda Valley Apt. 934",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:28.750718+00:00",
    id: "T3JkZXI6MTI=",
    number: "12",
    paymentStatus: PaymentStatusEnum.PREAUTH,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 298.76,
        currency: "USD"
      }
    },
    userEmail: "denise.freeman@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Thomasburgh",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "DJ",
        country: "Dżibuti"
      },
      countryArea: "",
      firstName: "James",
      id: "QWRkcmVzczo2",
      lastName: "Ball",
      phone: "",
      postalCode: "70958",
      streetAddress1: "60049 Fisher Grove",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:28.598246+00:00",
    id: "T3JkZXI6MTE=",
    number: "11",
    paymentStatus: PaymentStatusEnum.CONFIRMED,
    status: OrderStatus.UNFULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 663.69,
        currency: "USD"
      }
    },
    userEmail: "james.ball@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Lake Walter",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "MK",
        country: "Macedonia"
      },
      countryArea: "",
      firstName: "Michael",
      id: "QWRkcmVzczoz",
      lastName: "Martinez",
      phone: "",
      postalCode: "11343",
      streetAddress1: "843 Allen Ramp Suite 194",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:28.409836+00:00",
    id: "T3JkZXI6MTA=",
    number: "10",
    paymentStatus: PaymentStatusEnum.PREAUTH,
    status: OrderStatus.CANCELED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 280.41,
        currency: "USD"
      }
    },
    userEmail: "michael.martinez@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "West Patriciastad",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "SB",
        country: "Wyspy Salomona"
      },
      countryArea: "",
      firstName: "Melissa",
      id: "QWRkcmVzczoyNQ==",
      lastName: "Simon",
      phone: "",
      postalCode: "66272",
      streetAddress1: "487 Roberto Shores",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:28.185874+00:00",
    id: "T3JkZXI6OQ==",
    number: "9",
    paymentStatus: PaymentStatusEnum.PREAUTH,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 234.93,
        currency: "USD"
      }
    },
    userEmail: "melissa.simon@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Lake Kevinchester",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "CL",
        country: "Chile"
      },
      countryArea: "",
      firstName: "Justin",
      id: "QWRkcmVzczoyNA==",
      lastName: "Mccoy",
      phone: "",
      postalCode: "03826",
      streetAddress1: "74416 Jensen Gateway Suite 140",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:27.953588+00:00",
    id: "T3JkZXI6OA==",
    number: "8",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 485.19,
        currency: "USD"
      }
    },
    userEmail: "justin.mccoy@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "New Morganshire",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "NL",
        country: "Holandia"
      },
      countryArea: "",
      firstName: "Anthony",
      id: "QWRkcmVzczo3",
      lastName: "Gonzalez",
      phone: "",
      postalCode: "78701",
      streetAddress1: "402 Mason Viaduct Suite 592",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:27.828033+00:00",
    id: "T3JkZXI6Nw==",
    number: "7",
    paymentStatus: PaymentStatusEnum.CONFIRMED,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 223.54,
        currency: "USD"
      }
    },
    userEmail: "anthony.gonzalez@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Gabrielchester",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "SN",
        country: "Senegal"
      },
      countryArea: "",
      firstName: "Bradley",
      id: "QWRkcmVzczoyMw==",
      lastName: "Ford",
      phone: "",
      postalCode: "88661",
      streetAddress1: "56414 Ashley Gardens",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:27.636741+00:00",
    id: "T3JkZXI6Ng==",
    number: "6",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 237.55,
        currency: "USD"
      }
    },
    userEmail: "bradley.ford@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "East Steven",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "CG",
        country: "Kongo"
      },
      countryArea: "",
      firstName: "David",
      id: "QWRkcmVzczoxNg==",
      lastName: "Lawson",
      phone: "",
      postalCode: "87510",
      streetAddress1: "151 Huang Pines",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:27.420590+00:00",
    id: "T3JkZXI6NQ==",
    number: "5",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 453.55,
        currency: "USD"
      }
    },
    userEmail: "david.lawson@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "East Daniel",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "NA",
        country: "Namibia"
      },
      countryArea: "",
      firstName: "Lauren",
      id: "QWRkcmVzczoyMg==",
      lastName: "Watson",
      phone: "",
      postalCode: "22102",
      streetAddress1: "340 Amanda Tunnel Suite 869",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:27.230990+00:00",
    id: "T3JkZXI6NA==",
    number: "4",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 812.67,
        currency: "USD"
      }
    },
    userEmail: "lauren.watson@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Lake Margaret",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "CO",
        country: "Kolumbia"
      },
      countryArea: "",
      firstName: "Mark",
      id: "QWRkcmVzczoxNQ==",
      lastName: "Lee",
      phone: "",
      postalCode: "18829",
      streetAddress1: "34480 Daniel Centers Apt. 642",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:26.972507+00:00",
    id: "T3JkZXI6Mw==",
    number: "3",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 481.41,
        currency: "USD"
      }
    },
    userEmail: "mark.lee@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Dorothyberg",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "BJ",
        country: "Benin"
      },
      countryArea: "",
      firstName: "Kara",
      id: "QWRkcmVzczoyMQ==",
      lastName: "Murphy",
      phone: "",
      postalCode: "88138",
      streetAddress1: "0674 Kent Station Suite 395",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:26.751359+00:00",
    id: "T3JkZXI6Mg==",
    number: "2",
    paymentStatus: PaymentStatusEnum.CONFIRMED,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 569.19,
        currency: "USD"
      }
    },
    userEmail: "kara.murphy@example.com"
  },
  {
    __typename: "Order",
    billingAddress: {
      __typename: "Address",
      city: "Gregorymouth",
      cityArea: "",
      companyName: "",
      country: {
        __typename: "CountryDisplay",
        code: "CV",
        country: "Republika Zielonego Przylądka"
      },
      countryArea: "",
      firstName: "Curtis",
      id: "QWRkcmVzczox",
      lastName: "Bailey",
      phone: "",
      postalCode: "84525",
      streetAddress1: "839 Scott Lake",
      streetAddress2: ""
    },
    created: "2018-09-11T09:37:26.314968+00:00",
    id: "T3JkZXI6MQ==",
    number: "1",
    paymentStatus: PaymentStatusEnum.WAITING,
    status: OrderStatus.PARTIALLY_FULFILLED,
    total: {
      __typename: "TaxedMoney",
      gross: {
        __typename: "Money",
        amount: 557,
        currency: "USD"
      }
    },
    userEmail: "curtis.bailey@example.com"
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
    phone: "",
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
    phone: "",
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
