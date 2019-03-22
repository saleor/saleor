import { transformOrderStatus, transformPaymentStatus } from "../misc";
import {
  FulfillmentStatus,
  OrderAction,
  OrderEvents,
  OrderStatus,
  PaymentChargeStatusEnum
} from "../types/globalTypes";
import { OrderDetails_order } from "./types/OrderDetails";
import { OrderList_orders_edges_node } from "./types/OrderList";
import { UserSearch_customers_edges_node } from "./types/UserSearch";

export const clients: UserSearch_customers_edges_node[] = [
  {
    __typename: "User" as "User",
    email: "test.client1@example.com",
    id: "c1"
  },
  {
    __typename: "User" as "User",
    email: "test.client2@example.com",
    id: "c2"
  },
  {
    __typename: "User" as "User",
    email: "test.client3@example.com",
    id: "c3"
  },
  {
    __typename: "User" as "User",
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
    paymentStatus: PaymentChargeStatusEnum.FULLY_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.FULLY_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.FULLY_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.FULLY_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.FULLY_CHARGED,
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
    paymentStatus: PaymentChargeStatusEnum.FULLY_CHARGED,
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
export const order = (placeholder: string): OrderDetails_order => ({
  __typename: "Order",
  actions: [
    OrderAction.CAPTURE,
    OrderAction.MARK_AS_PAID,
    OrderAction.REFUND,
    OrderAction.VOID
  ],
  availableShippingMethods: [
    {
      __typename: "ShippingMethod",
      id: "U2hpcHBpbmdNZXRob2Q6NQ==",
      name: "FBA",
      price: {
        __typename: "Money",
        amount: 12.41,
        currency: "USD"
      }
    },
    {
      __typename: "ShippingMethod",
      id: "U2hpcHBpbmdNZXRob2Q6Nw==",
      name: "Oceania Air Mail",
      price: {
        __typename: "Money",
        amount: 9.12,
        currency: "USD"
      }
    },
    {
      __typename: "ShippingMethod",
      id: "U2hpcHBpbmdNZXRob2Q6Ng==",
      name: "FedEx Express",
      price: {
        __typename: "Money",
        amount: 7.6,
        currency: "USD"
      }
    }
  ],
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
  canFinalize: true,
  created: "2018-09-11T09:37:28.185874+00:00",
  customerNote: "Lorem ipsum dolor sit amet",
  events: [
    {
      __typename: "OrderEvent",
      amount: null,
      date: "2018-09-17T13:22:24.376193+00:00",
      email: null,
      emailType: null,
      id: "T3JkZXJFdmVudDoyMQ==",
      message: null,
      quantity: 1,
      type: OrderEvents.FULFILLMENT_FULFILLED_ITEMS,
      user: {
        __typename: "User",
        email: "admin@example.com",
        id: "QWRkcmVzczoxNQ=="
      }
    }
  ],
  fulfillments: [
    {
      __typename: "Fulfillment",
      fulfillmentOrder: 2,
      id: "RnVsZmlsbG1lbnQ6MjQ=",
      lines: [
        {
          __typename: "FulfillmentLine",
          id: "RnVsZmlsbG1lbnRMaW5lOjM5",
          orderLine: {
            __typename: "OrderLine",
            id: "T3JkZXJMaW5lOjIz",
            isShippingRequired: false,
            productName: "Williams, Garcia and Walker (XS)",
            productSku: "5-1337",
            quantity: 2,
            quantityFulfilled: 2,
            thumbnailUrl: placeholder,
            unitPrice: {
              __typename: "TaxedMoney",
              gross: {
                __typename: "Money",
                amount: 79.71,
                currency: "USD"
              },
              net: {
                __typename: "Money",
                amount: 79.71,
                currency: "USD"
              }
            }
          },
          quantity: 1
        }
      ],
      status: FulfillmentStatus.FULFILLED,
      trackingNumber: ""
    },
    {
      __typename: "Fulfillment",
      fulfillmentOrder: 1,
      id: "RnVsZmlsbG1lbnQ6OQ==",
      lines: [
        {
          __typename: "FulfillmentLine",
          id: "RnVsZmlsbG1lbnRMaW5lOjE1",
          orderLine: {
            __typename: "OrderLine",
            id: "T3JkZXJMaW5lOjIz",
            isShippingRequired: false,
            productName: "Williams, Garcia and Walker (XS)",
            productSku: "5-1337",
            quantity: 2,
            quantityFulfilled: 2,
            thumbnailUrl: placeholder,
            unitPrice: {
              __typename: "TaxedMoney",
              gross: {
                __typename: "Money",
                amount: 79.71,
                currency: "USD"
              },
              net: {
                __typename: "Money",
                amount: 79.71,
                currency: "USD"
              }
            }
          },
          quantity: 1
        }
      ],
      status: FulfillmentStatus.FULFILLED,
      trackingNumber: ""
    }
  ],
  id: "T3JkZXI6OQ==",
  lines: [
    {
      __typename: "OrderLine",
      id: "T3JkZXJMaW5lOjIy",
      isShippingRequired: true,
      productName: "Watkins-Gonzalez (Soft)",
      productSku: "59-1337",
      quantity: 3,
      quantityFulfilled: 0,
      thumbnailUrl: placeholder,
      unitPrice: {
        __typename: "TaxedMoney",
        gross: {
          __typename: "Money",
          amount: 18.51,
          currency: "USD"
        },
        net: {
          __typename: "Money",
          amount: 18.51,
          currency: "USD"
        }
      }
    },
    {
      __typename: "OrderLine",
      id: "T3JkZXJMaW5lOjIz",
      isShippingRequired: true,
      productName: "Williams, Garcia and Walker (XS)",
      productSku: "5-1337",
      quantity: 2,
      quantityFulfilled: 2,
      thumbnailUrl: placeholder,
      unitPrice: {
        __typename: "TaxedMoney",
        gross: {
          __typename: "Money",
          amount: 79.71,
          currency: "USD"
        },
        net: {
          __typename: "Money",
          amount: 79.71,
          currency: "USD"
        }
      }
    }
  ],
  number: "9",
  paymentStatus: PaymentChargeStatusEnum.NOT_CHARGED,
  shippingAddress: {
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
  shippingMethod: null,
  shippingMethodName: "Registred priority",
  shippingPrice: {
    __typename: "TaxedMoney",
    gross: {
      __typename: "Money",
      amount: 19.98,
      currency: "USD"
    }
  },
  status: OrderStatus.PARTIALLY_FULFILLED,
  subtotal: {
    __typename: "TaxedMoney",
    gross: {
      __typename: "Money",
      amount: 214.95,
      currency: "USD"
    }
  },
  total: {
    __typename: "TaxedMoney",
    gross: {
      __typename: "Money",
      amount: 234.93,
      currency: "USD"
    },
    tax: {
      __typename: "Money",
      amount: 0,
      currency: "USD"
    }
  },
  totalAuthorized: {
    __typename: "Money",
    amount: 234.93,
    currency: "USD"
  },
  totalCaptured: {
    __typename: "Money",
    amount: 0,
    currency: "USD"
  },
  user: null,
  userEmail: "melissa.simon@example.com"
});
export const draftOrder = (placeholder: string): OrderDetails_order => ({
  __typename: "Order" as "Order",
  actions: [OrderAction.CAPTURE],
  availableShippingMethods: null,
  billingAddress: null,
  canFinalize: true,
  created: "2018-09-20T23:23:39.811428+00:00",
  customerNote: "Lorem ipsum dolor sit",
  events: [],
  fulfillments: [],
  id: "T3JkZXI6MjQ=",
  lines: [
    {
      __typename: "OrderLine" as "OrderLine",
      id: "T3JkZXJMaW5lOjQ1",
      isShippingRequired: false,
      productName: "Davis Group (Hard)",
      productSku: "58-1338",
      quantity: 2,
      quantityFulfilled: 0,
      thumbnailUrl: placeholder,
      unitPrice: {
        __typename: "TaxedMoney" as "TaxedMoney",
        gross: {
          __typename: "Money" as "Money",
          amount: 65.95,
          currency: "USD"
        },
        net: {
          __typename: "Money" as "Money",
          amount: 65.95,
          currency: "USD"
        }
      }
    },
    {
      __typename: "OrderLine" as "OrderLine",
      id: "T3JkZXJMaW5lOjQ2",
      isShippingRequired: false,
      productName: "Anderson PLC (15-1337)",
      productSku: "15-1337",
      quantity: 2,
      quantityFulfilled: 0,
      thumbnailUrl: placeholder,
      unitPrice: {
        __typename: "TaxedMoney" as "TaxedMoney",
        gross: {
          __typename: "Money" as "Money",
          amount: 68.2,
          currency: "USD"
        },
        net: {
          __typename: "Money" as "Money",
          amount: 68.2,
          currency: "USD"
        }
      }
    }
  ],
  number: "24",
  paymentStatus: null,
  shippingAddress: null,
  shippingMethod: null,
  shippingMethodName: null,
  shippingPrice: {
    __typename: "TaxedMoney" as "TaxedMoney",
    gross: {
      __typename: "Money" as "Money",
      amount: 0,
      currency: "USD"
    }
  },
  status: "DRAFT" as OrderStatus.DRAFT,
  subtotal: {
    __typename: "TaxedMoney" as "TaxedMoney",
    gross: {
      __typename: "Money" as "Money",
      amount: 168.3,
      currency: "USD"
    }
  },
  total: {
    __typename: "TaxedMoney" as "TaxedMoney",
    gross: {
      __typename: "Money" as "Money",
      amount: 168.3,
      currency: "USD"
    },
    tax: {
      __typename: "Money" as "Money",
      amount: 68.3,
      currency: "USD"
    }
  },
  totalAuthorized: null,
  totalCaptured: null,
  user: null,
  userEmail: null
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
export const orderLineSearch = (placeholderImage: string) => [
  {
    __typename: "Product" as "Product",
    id: "UHJvZHVjdDo3Mg==",
    name: "Apple Juice",
    thumbnail: {
      __typename: "Image" as "Image",
      url: placeholderImage
    },
    variants: [
      {
        __typename: "ProductVariant" as "ProductVariant",
        id: "UHJvZHVjdFZhcmlhbnQ6MjAy",
        name: "500ml",
        price: { amount: 3.0, currency: "USD", __typename: "Money" as "Money" },
        sku: "93855755"
      },
      {
        __typename: "ProductVariant" as "ProductVariant",
        id: "UHJvZHVjdFZhcmlhbnQ6MjAz",
        name: "1l",
        price: { amount: 5.0, currency: "USD", __typename: "Money" as "Money" },
        sku: "43226647"
      },
      {
        __typename: "ProductVariant" as "ProductVariant",
        id: "UHJvZHVjdFZhcmlhbnQ6MjA0",
        name: "2l",
        price: { amount: 7.0, currency: "USD", __typename: "Money" as "Money" },
        sku: "80884671"
      }
    ]
  },
  {
    __typename: "Product" as "Product",
    id: "UHJvZHVjdDo3NQ==",
    name: "Pineapple Juice",
    thumbnail: {
      __typename: "Image" as "Image",
      url: placeholderImage
    },
    variants: [
      {
        __typename: "ProductVariant" as "ProductVariant",
        id: "UHJvZHVjdFZhcmlhbnQ6MjEx",
        name: "500ml",
        price: { amount: 3.0, currency: "USD", __typename: "Money" as "Money" },
        sku: "43200242"
      },
      {
        __typename: "ProductVariant" as "ProductVariant",
        id: "UHJvZHVjdFZhcmlhbnQ6MjEy",
        name: "1l",
        price: { amount: 5.0, currency: "USD", __typename: "Money" as "Money" },
        sku: "79129513"
      },
      {
        __typename: "ProductVariant" as "ProductVariant",
        id: "UHJvZHVjdFZhcmlhbnQ6MjEz",
        name: "2l",
        price: { amount: 7.0, currency: "USD", __typename: "Money" as "Money" },
        sku: "75799450"
      }
    ]
  }
];
