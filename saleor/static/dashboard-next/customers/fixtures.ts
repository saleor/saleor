import { PaymentChargeStatusEnum } from "../types/globalTypes";
import { CustomerAddresses_user } from "./types/CustomerAddresses";
import { CustomerDetails_user } from "./types/CustomerDetails";
import { ListCustomers_customers_edges_node } from "./types/ListCustomers";

export const customers = [
  {
    dateJoined: "2017-10-11T13:22:30.831Z",
    defaultBillingAddress: {
      city: "Thompsontown",
      cityArea: "Rhode Island",
      companyName: null,
      country: {
        code: "SW",
        country: "Swaziland"
      },
      countryArea: "Buckinghamshire",
      firstName: "Alexander",
      id: "52402",
      lastName: "Simonis",
      phone: "+17 253-928-8945",
      postalCode: "47639-5237",
      streetAddress1: "83772 Savanah Summit",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "West Bret",
      cityArea: "North Dakota",
      companyName: null,
      country: {
        code: "SD",
        country: "Sudan"
      },
      countryArea: null,
      firstName: "Alexander",
      id: "77109",
      lastName: "Simonis",
      phone: "+21 463-243-6545",
      postalCode: "21665",
      streetAddress1: "780 Jaime Prairie",
      streetAddress2: null
    },
    email: "alexander_simonis@example.com",
    id: "11810",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2018-01-21T22:41:38.241Z",
    defaultBillingAddress: {
      city: "Lake Adela",
      cityArea: "Maryland",
      companyName: "Kemmer Group",
      country: {
        code: "KE",
        country: "Kenya"
      },
      countryArea: null,
      firstName: "Augustus",
      id: "81868",
      lastName: "Crist",
      phone: "+19 583-374-8576",
      postalCode: "29966",
      streetAddress1: "5656 Crooks Park",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "East Brandttown",
      cityArea: "Missouri",
      companyName: null,
      country: {
        code: "SO",
        country: "Somalia"
      },
      countryArea: null,
      firstName: "Augustus",
      id: "11788",
      lastName: "Crist",
      phone: "+52 584-961-3073",
      postalCode: "80218",
      streetAddress1: "37212 O'Reilly Ford",
      streetAddress2: null
    },
    email: "augustus_crist@example.com",
    id: "34351",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2018-01-19T21:36:19.298Z",
    defaultBillingAddress: {
      city: "East Raymond",
      cityArea: "Delaware",
      companyName: null,
      country: {
        code: "SM",
        country: "San Marino"
      },
      countryArea: null,
      firstName: "Kelton",
      id: "77939",
      lastName: "Eichmann",
      phone: "+17 650-119-2676",
      postalCode: "94747-5311",
      streetAddress1: "5060 Aufderhar Common",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "East Raymond",
      cityArea: "Delaware",
      companyName: null,
      country: {
        code: "SM",
        country: "San Marino"
      },
      countryArea: null,
      firstName: "Kelton",
      id: "77939",
      lastName: "Eichmann",
      phone: "+17 650-119-2676",
      postalCode: "94747-5311",
      streetAddress1: "5060 Aufderhar Common",
      streetAddress2: null
    },
    email: "kelton_eichmann@example.com",
    id: "47883",
    isActive: true,
    isStaff: true,
    note: null
  },
  {
    dateJoined: "2018-01-18T15:08:59.535Z",
    defaultBillingAddress: {
      city: "Torphyton",
      cityArea: "Iowa",
      companyName: null,
      country: {
        code: "CD",
        country: "Chad"
      },
      countryArea: null,
      firstName: "Magnolia",
      id: "2237",
      lastName: "Brakus",
      phone: "+52 136-461-3995",
      postalCode: "64573",
      streetAddress1: "106 Swift Squares",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Torphyton",
      cityArea: "Iowa",
      companyName: null,
      country: {
        code: "CD",
        country: "Chad"
      },
      countryArea: null,
      firstName: "Magnolia",
      id: "2237",
      lastName: "Brakus",
      phone: "+52 136-461-3995",
      postalCode: "64573",
      streetAddress1: "106 Swift Squares",
      streetAddress2: null
    },
    email: "magnolia_brakus@example.com",
    id: "53433",
    isActive: true,
    isStaff: false,
    note: "Dolorem qui vero iure."
  },
  {
    dateJoined: "2017-07-22T05:21:13.774Z",
    defaultBillingAddress: {
      city: "Port Savanahfort",
      cityArea: "Nebraska",
      companyName: null,
      country: {
        code: "GD",
        country: "Greenland"
      },
      countryArea: null,
      firstName: "Adonis",
      id: "10532",
      lastName: "Pacocha",
      phone: "+11 944-018-0185",
      postalCode: "52460-3432",
      streetAddress1: "32181 Lindgren Turnpike",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "East Fletcher",
      cityArea: "New Hampshire",
      companyName: null,
      country: {
        code: "KR",
        country: "Kyrgyz Republic"
      },
      countryArea: null,
      firstName: "Adonis",
      id: "45425",
      lastName: "Pacocha",
      phone: "+36 549-984-7736",
      postalCode: "29123-8368",
      streetAddress1: "938 Jordyn Harbor",
      streetAddress2: null
    },
    email: "adonis_pacocha@example.com",
    id: "42657",
    isActive: true,
    isStaff: false,
    note: "Unde qui et."
  },
  {
    dateJoined: "2018-05-31T06:55:23.938Z",
    defaultBillingAddress: {
      city: "Reykjavik",
      cityArea: "Höfuðborgarsvæði",
      companyName: null,
      country: {
        code: "IS",
        country: "Iceland"
      },
      countryArea: null,
      firstName: "Carlie",
      id: "83778",
      lastName: "Walsh",
      phone: "+27 387-984-3969",
      postalCode: "48003",
      streetAddress1: "08030 Corrine Row",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "North Tanyafurt",
      cityArea: "Wyoming",
      companyName: null,
      country: {
        code: "RW",
        country: "Rwanda"
      },
      countryArea: null,
      firstName: "Carlie",
      id: "14941",
      lastName: "Walsh",
      phone: "+44 320-941-3747",
      postalCode: "33296",
      streetAddress1: "1231 Eriberto Stravenue",
      streetAddress2: null
    },
    email: "carlie_walsh@example.com",
    id: "93594",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2017-08-26T08:37:16.497Z",
    defaultBillingAddress: {
      city: "Labadiechester",
      cityArea: "Iowa",
      companyName: null,
      country: {
        code: "MA",
        country: "Morocco"
      },
      countryArea: "Buckinghamshire",
      firstName: "Junius",
      id: "86163",
      lastName: "Crist",
      phone: "+47 605-434-6759",
      postalCode: "39521",
      streetAddress1: "333 Bernie Fords",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Kaylistad",
      cityArea: "Louisiana",
      companyName: null,
      country: {
        code: "EG",
        country: "Equatorial Guinea"
      },
      countryArea: "Bedfordshire",
      firstName: "Junius",
      id: "78537",
      lastName: "Crist",
      phone: "+20 893-019-4257",
      postalCode: "43886-6932",
      streetAddress1: "0597 Angeline Gateway",
      streetAddress2: null
    },
    email: "junius_crist@example.com",
    id: "70932",
    isActive: true,
    isStaff: false,
    note: "Et cumque consequatur aliquam."
  },
  {
    dateJoined: "2018-01-08T11:55:39.220Z",
    defaultBillingAddress: {
      city: "Lydiahaven",
      cityArea: "Arkansas",
      companyName: null,
      country: {
        code: "CB",
        country: "Cambodia"
      },
      countryArea: "Berkshire",
      firstName: "Pedro",
      id: "70545",
      lastName: "Harvey",
      phone: "+35 817-342-0603",
      postalCode: "72196",
      streetAddress1: "9280 Asa Center",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Lydiahaven",
      cityArea: "Arkansas",
      companyName: null,
      country: {
        code: "CB",
        country: "Cambodia"
      },
      countryArea: "Berkshire",
      firstName: "Pedro",
      id: "70545",
      lastName: "Harvey",
      phone: "+35 817-342-0603",
      postalCode: "72196",
      streetAddress1: "9280 Asa Center",
      streetAddress2: null
    },
    email: "pedro_harvey@example.com",
    id: "61255",
    isActive: false,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2017-07-28T00:49:40.975Z",
    defaultBillingAddress: {
      city: "East Leilafurt",
      cityArea: "Arizona",
      companyName: null,
      country: {
        code: "BG",
        country: "Bulgaria"
      },
      countryArea: null,
      firstName: "Raven",
      id: "9167",
      lastName: "Deckow",
      phone: "+62 210-019-3184",
      postalCode: "02296",
      streetAddress1: "8546 Marks Highway",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "South Hendersonbury",
      cityArea: "Nevada",
      companyName: "Raynor Inc",
      country: {
        code: "TK",
        country: "Turkmenistan"
      },
      countryArea: null,
      firstName: "Raven",
      id: "48467",
      lastName: "Deckow",
      phone: "+46 654-130-2375",
      postalCode: "00611",
      streetAddress1: "87001 Howell Forge",
      streetAddress2: null
    },
    email: "raven_deckow@example.com",
    id: "84610",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2018-05-04T03:17:55.298Z",
    defaultBillingAddress: {
      city: "Windlerton",
      cityArea: "Texas",
      companyName: "Heller, Bauch and Friesen",
      country: {
        code: "AN",
        country: "Andorra"
      },
      countryArea: null,
      firstName: "Paige",
      id: "63622",
      lastName: "Lesch",
      phone: "+08 972-463-2863",
      postalCode: "80681-4790",
      streetAddress1: "93719 Hackett Mountain",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Windlerton",
      cityArea: "Texas",
      companyName: "Heller, Bauch and Friesen",
      country: {
        code: "AN",
        country: "Andorra"
      },
      countryArea: null,
      firstName: "Paige",
      id: "63622",
      lastName: "Lesch",
      phone: "+08 972-463-2863",
      postalCode: "80681-4790",
      streetAddress1: "93719 Hackett Mountain",
      streetAddress2: null
    },
    email: "paige_lesch@example.com",
    id: "28741",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2018-01-27T13:43:07.363Z",
    defaultBillingAddress: {
      city: "Gleichnerborough",
      cityArea: "Missouri",
      companyName: null,
      country: {
        code: "DM",
        country: "Dominica"
      },
      countryArea: null,
      firstName: "Santino",
      id: "89962",
      lastName: "Bins",
      phone: "+45 844-752-5593",
      postalCode: "33593-8299",
      streetAddress1: "557 Jacobi Gateway",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "West Jolieland",
      cityArea: "Connecticut",
      companyName: null,
      country: {
        code: "SH",
        country: "Saint Helena"
      },
      countryArea: "Bedfordshire",
      firstName: "Santino",
      id: "58915",
      lastName: "Bins",
      phone: "+25 685-424-9436",
      postalCode: "58377",
      streetAddress1: "6647 Kody Locks",
      streetAddress2: null
    },
    email: "santino_bins@example.com",
    id: "46991",
    isActive: false,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2018-03-13T22:04:39.414Z",
    defaultBillingAddress: {
      city: "North Sister",
      cityArea: "Ohio",
      companyName: null,
      country: {
        code: "BN",
        country: "Bangladesh"
      },
      countryArea: "Bedfordshire",
      firstName: "Quinn",
      id: "94894",
      lastName: "Barrows",
      phone: "+35 995-317-3324",
      postalCode: "41805",
      streetAddress1: "146 Dee Station",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "North Sister",
      cityArea: "Ohio",
      companyName: null,
      country: {
        code: "BN",
        country: "Bangladesh"
      },
      countryArea: "Bedfordshire",
      firstName: "Quinn",
      id: "94894",
      lastName: "Barrows",
      phone: "+35 995-317-3324",
      postalCode: "41805",
      streetAddress1: "146 Dee Station",
      streetAddress2: null
    },
    email: "quinn_barrows@example.com",
    id: "50687",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2018-01-27T01:40:52.437Z",
    defaultBillingAddress: {
      city: "Kenstad",
      cityArea: "Alabama",
      companyName: null,
      country: {
        code: "UA",
        country: "United Arab Emirates"
      },
      countryArea: null,
      firstName: "Berry",
      id: "93575",
      lastName: "Windler",
      phone: "+41 876-373-9137",
      postalCode: "89880-6342",
      streetAddress1: "01419 Bernhard Plain",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Kenstad",
      cityArea: "Alabama",
      companyName: null,
      country: {
        code: "UA",
        country: "United Arab Emirates"
      },
      countryArea: null,
      firstName: "Berry",
      id: "93575",
      lastName: "Windler",
      phone: "+41 876-373-9137",
      postalCode: "89880-6342",
      streetAddress1: "01419 Bernhard Plain",
      streetAddress2: null
    },
    email: "berry_windler@example.com",
    id: "36798",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2017-07-17T22:43:18.274Z",
    defaultBillingAddress: {
      city: "Jamilstad",
      cityArea: "Idaho",
      companyName: "Kilback - Crooks",
      country: {
        code: "UR",
        country: "Uruguay"
      },
      countryArea: null,
      firstName: "Johnathon",
      id: "78744",
      lastName: "Kohler",
      phone: "+63 888-798-4522",
      postalCode: "43892-8110",
      streetAddress1: "287 Rowe Mews",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Jamilstad",
      cityArea: "Idaho",
      companyName: "Kilback - Crooks",
      country: {
        code: "UR",
        country: "Uruguay"
      },
      countryArea: null,
      firstName: "Johnathon",
      id: "78744",
      lastName: "Kohler",
      phone: "+63 888-798-4522",
      postalCode: "43892-8110",
      streetAddress1: "287 Rowe Mews",
      streetAddress2: null
    },
    email: "johnathon_kohler@example.com",
    id: "98483",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2017-07-10T00:09:56.552Z",
    defaultBillingAddress: {
      city: "Keltonland",
      cityArea: "West Virginia",
      companyName: "Bailey, Barrows and Prosacco",
      country: {
        code: "DN",
        country: "Denmark"
      },
      countryArea: null,
      firstName: "Linwood",
      id: "19005",
      lastName: "Windler",
      phone: "+60 815-222-0791",
      postalCode: "12595",
      streetAddress1: "496 Sporer Mountain",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Keltonland",
      cityArea: "West Virginia",
      companyName: "Bailey, Barrows and Prosacco",
      country: {
        code: "DN",
        country: "Denmark"
      },
      countryArea: null,
      firstName: "Linwood",
      id: "19005",
      lastName: "Windler",
      phone: "+60 815-222-0791",
      postalCode: "12595",
      streetAddress1: "496 Sporer Mountain",
      streetAddress2: null
    },
    email: "linwood_windler@example.com",
    id: "18050",
    isActive: true,
    isStaff: false,
    note: null
  },
  {
    dateJoined: "2017-08-25T06:08:19.951Z",
    defaultBillingAddress: {
      city: "West Feliciamouth",
      cityArea: "Montana",
      companyName: null,
      country: {
        code: "JA",
        country: "Japan"
      },
      countryArea: null,
      firstName: "Timmy",
      id: "33855",
      lastName: "Macejkovic",
      phone: "+41 460-907-9374",
      postalCode: "15926",
      streetAddress1: "0238 Cremin Freeway",
      streetAddress2: null
    },
    defaultShippingAddress: {
      city: "Larkinstad",
      cityArea: "California",
      companyName: null,
      country: {
        code: "SO",
        country: "Somalia"
      },
      countryArea: null,
      firstName: "Timmy",
      id: "67467",
      lastName: "Macejkovic",
      phone: "+64 943-882-1295",
      postalCode: "43425",
      streetAddress1: "96332 Corkery Lane",
      streetAddress2: null
    },
    email: "timmy_macejkovic@example.com",
    id: "65578",
    isActive: true,
    isStaff: false,
    note: "Dolorem vitae."
  }
];

export const customerList: ListCustomers_customers_edges_node[] = [
  {
    __typename: "User",
    email: "Curtis.bailey@example.com",
    firstName: "curtis",
    id: "VXNlcjox",
    lastName: "Bailey",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 2
    }
  },
  {
    __typename: "User",
    email: "curtis.bailey@example.com",
    firstName: "Curtis",
    id: "VXNlcjox",
    lastName: "Bailey",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 2
    }
  },
  {
    __typename: "User",
    email: "elizabeth.vaughn@example.com",
    firstName: "Elizabeth",
    id: "VXNlcjoy",
    lastName: "Vaughn",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 1
    }
  },
  {
    __typename: "User",
    email: "michael.martinez@example.com",
    firstName: "Michael",
    id: "VXNlcjoz",
    lastName: "Martinez",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 1
    }
  },
  {
    __typename: "User",
    email: "kayla.griffin@example.com",
    firstName: "Kayla",
    id: "VXNlcjo0",
    lastName: "Griffin",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "donna.robinson@example.com",
    firstName: "Donna",
    id: "VXNlcjo1",
    lastName: "Robinson",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "james.ball@example.com",
    firstName: "James",
    id: "VXNlcjo2",
    lastName: "Bqall",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 1
    }
  },
  {
    __typename: "User",
    email: "anthony.gonzalez@example.com",
    firstName: "Anthony",
    id: "VXNlcjo3",
    lastName: "Gonzalez",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 2
    }
  },
  {
    __typename: "User",
    email: "anthony.gonzalez@example.com",
    firstName: "Anthony",
    id: "VXNlcjo3",
    lastName: "Gonzalez",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 2
    }
  },
  {
    __typename: "User",
    email: "wesley.davis@example.com",
    firstName: "Wesley",
    id: "VXNlcjo4",
    lastName: "Davis",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 1
    }
  },
  {
    __typename: "User",
    email: "laura.stone@example.com",
    firstName: "Laura",
    id: "VXNlcjo5",
    lastName: "Stone",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 1
    }
  },
  {
    __typename: "User",
    email: "william.miller@example.com",
    firstName: "William",
    id: "VXNlcjoxMA==",
    lastName: "Miller",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "donald.solomon@example.com",
    firstName: "Donald",
    id: "VXNlcjoxMQ==",
    lastName: "Solomon",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "anthony.young@example.com",
    firstName: "Anthony",
    id: "VXNlcjoxMg==",
    lastName: "Young",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "sharon.hanson@example.com",
    firstName: "Hanson",
    id: "VXNlcjoxMw==",
    lastName: "Sharon",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "laura.jensen@example.com",
    firstName: "Laura",
    id: "VXNlcjoxNA==",
    lastName: "Jensen",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 1
    }
  },
  {
    __typename: "User",
    email: "mark.lee@example.com",
    firstName: "Mark",
    id: "VXNlcjoxNQ==",
    lastName: "Lee",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 1
    }
  },
  {
    __typename: "User",
    email: "david.lawson@example.com",
    firstName: "David",
    id: "VXNlcjoxNg==",
    lastName: "Lawson",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 2
    }
  },
  {
    __typename: "User",
    email: "david.lawson@example.com",
    firstName: "David",
    id: "VXNlcjoxNg==",
    lastName: "Lawson",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 2
    }
  },
  {
    __typename: "User",
    email: "faith.smith@example.com",
    firstName: "Faith",
    id: "VXNlcjoxNw==",
    lastName: "Smith",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "john.jones@example.com",
    firstName: "John",
    id: "VXNlcjoxOA==",
    lastName: "Jones",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "ronald.fisher@example.com",
    firstName: "Ronald",
    id: "VXNlcjoxOQ==",
    lastName: "Fisher",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "jason.gray@example.com",
    firstName: "Jason",
    id: "VXNlcjoyMA==",
    lastName: "Gray",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 0
    }
  },
  {
    __typename: "User",
    email: "admin@example.com",
    firstName: "Tom",
    id: "VXNlcjoyMQ==",
    lastName: "Cooper",
    orders: {
      __typename: "OrderCountableConnection",
      totalCount: 6
    }
  }
];
export const customer: CustomerDetails_user & CustomerAddresses_user = {
  __typename: "User",
  addresses: [
    {
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
      streetAddress2: "0238 Cremin Freeway"
    },
    {
      __typename: "Address",
      city: "West Feliciamouth",
      cityArea: "Montana",
      companyName: null,
      country: {
        __typename: "CountryDisplay",
        code: "JA",
        country: "Japan"
      },
      countryArea: null,
      firstName: "Timmy",
      id: "33855",
      lastName: "Macejkovic",
      phone: "+41 460-907-9374",
      postalCode: "15926",
      streetAddress1: "0238 Cremin Freeway",
      streetAddress2: null
    }
  ],
  dateJoined: "2017-05-07T09:37:30.124154+00:00",
  firstName: "Tom",

  defaultBillingAddress: {
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
  defaultShippingAddress: {
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
  email: "elizabeth.vaughn@example.com",
  id: "VXNlcjoy",
  isActive: true,
  lastLogin: "2018-05-07T09:37:30.124154+00:00",
  lastName: "Cooper",
  lastPlacedOrder: {
    __typename: "OrderCountableConnection",
    edges: [
      {
        __typename: "OrderCountableEdge",
        node: {
          __typename: "Order",
          created: "2018-05-07T09:37:30.124154+00:00",
          id: "T3JkZXI6MTk="
        }
      }
    ]
  },
  note: null,
  orders: {
    __typename: "OrderCountableConnection",
    edges: [
      {
        __typename: "OrderCountableEdge",
        node: {
          __typename: "Order",
          created: "2018-05-07T09:37:30.124154+00:00",
          id: "T3JkZXI6MTk=",
          number: "8234",
          paymentStatus: PaymentChargeStatusEnum.FULLY_CHARGED,
          total: {
            __typename: "TaxedMoney",
            gross: {
              __typename: "Money",
              amount: 1215.89,
              currency: "USD"
            }
          }
        }
      }
    ]
  }
};
