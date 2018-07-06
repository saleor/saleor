export const product = (placeholderImage: string) => ({
  id: "p10171",
  seoTitle: "Ergonomic Plastic Bacon",
  seoDescription: "Omnis rerum ea. Fugit dignissimos modi est rerum",
  productType: { id: "pt76406", name: "Versatile" },
  name: "Ergonomic Plastic Bacon",
  description:
    "Omnis rerum ea. Fugit dignissimos modi est rerum. Qui corrupti expedita et. Dolorem dolorum illo doloremque. Officia perspiciatis facilis ab maxime voluptatem eligendi ipsam. Quisquam impedit repudiandae eos. Id sit dolores adipisci qui omnis dolores qui. Illo deleniti mollitia perspiciatis.",
  sku: "59661-34207",
  category: { id: "Q2F0ZWdvcnk6MQ==", name: "Apparel" },
  collections: {
    edges: [{ node: { id: "Q29sbGVjdGlvbjoy", name: "Winter sale" } }]
  },
  price: { currency: "NZD", amount: 339.39, localized: "339.39 NZD" },
  availableOn: "2018-08-25T18:45:54.125Z",
  isPublished: true,
  attributes: [
    {
      attribute: {
        id: "pta18161",
        sortNumber: 0,
        name: "Borders",
        slug: "Borders",
        values: [
          { id: "ptav47282", sortNumber: 0, name: "portals", slug: "portals" },
          { id: "ptav17253", sortNumber: 1, name: "Baht", slug: "Baht" }
        ]
      },
      value: {
        id: "ptav47282",
        sortNumber: 0,
        name: "portals",
        slug: "portals"
      }
    },
    {
      attribute: {
        id: "pta22785",
        sortNumber: 1,
        name: "Legacy",
        slug: "Legacy",
        values: [
          { id: "ptav31282", sortNumber: 0, name: "payment", slug: "payment" },
          {
            id: "ptav14907",
            sortNumber: 1,
            name: "Auto Loan Account",
            slug: "Auto-Loan-Account"
          },
          { id: "ptav27366", sortNumber: 2, name: "Garden", slug: "Garden" },
          { id: "ptav11873", sortNumber: 3, name: "override", slug: "override" }
        ]
      },
      value: {
        id: "ptav14907",
        sortNumber: 1,
        name: "Auto Loan Account",
        slug: "Auto-Loan-Account"
      }
    }
  ],
  isFeatured: false,
  variants: {
    edges: [
      {
        node: {
          id: "pv75934",
          sku: "87192-94370",
          name: "Cordoba Oro",
          priceOverride: {
            amount: 678.78,
            currency: "USD",
            localized: "678.78 USD"
          },
          stockQuantity: 48,
          margin: 2
        }
      },
      {
        node: {
          id: "pv68615",
          sku: "69055-15190",
          name: "silver",
          priceOverride: null,
          stockQuantity: 14,
          margin: 7
        }
      }
    ]
  },
  thumbnailUrl: placeholderImage,
  images: {
    edges: [
      {
        node: {
          id: "UHJvZHVjdEltYWdlOjE=",
          sortOrder: 0,
          image: placeholderImage,
          url: placeholderImage
        }
      },
      {
        node: {
          id: "UHJvZHVjdEltYWdlOjE=",
          sortOrder: 2,
          image: placeholderImage,
          alt: "Id sit dolores adipisci",
          url: placeholderImage
        }
      }
    ]
  },
  availability: { available: false },
  purchaseCost: {
    start: { currency: "NZD", amount: 339.39, localized: "339.39 NZD" },
    stop: { currency: "NZD", amount: 678.78, localized: "678.78 NZD" }
  },
  margin: { start: 2, stop: 7 },
  url: "/example-url"
});
export const products = (placeholderImage: string) => [
  {
    id: "UHJvZHVjdDox",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholderImage,
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoy",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholderImage,
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoz",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholderImage,
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoa",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholderImage,
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  }
];

export const variant = (placeholderImage: string) => ({
  attributes: [
    {
      attribute: {
        id: "pta18161",
        sortNumber: 0,
        name: "Borders",
        slug: "Borders",
        values: [
          { id: "ptav47282", sortNumber: 0, name: "portals", slug: "portals" },
          { id: "ptav17253", sortNumber: 1, name: "Baht", slug: "Baht" }
        ]
      },
      value: {
        id: "ptav47282",
        sortNumber: 0,
        name: "portals",
        slug: "portals"
      }
    },
    {
      attribute: {
        id: "pta22785",
        sortNumber: 1,
        name: "Legacy",
        slug: "Legacy",
        values: [
          { id: "ptav31282", sortNumber: 0, name: "payment", slug: "payment" },
          {
            id: "ptav14907",
            sortNumber: 1,
            name: "Auto Loan Account",
            slug: "Auto-Loan-Account"
          },
          { id: "ptav27366", sortNumber: 2, name: "Garden", slug: "Garden" },
          { id: "ptav11873", sortNumber: 3, name: "override", slug: "override" }
        ]
      },
      value: {
        id: "ptav14907",
        sortNumber: 1,
        name: "Auto Loan Account",
        slug: "Auto-Loan-Account"
      }
    }
  ],
  images: {
    edges: [
      {
        node: {
          id: "img1"
        }
      },
      {
        node: {
          id: "img2"
        }
      },
      {
        node: {
          id: "img7"
        }
      },
      {
        node: {
          id: "img8"
        }
      }
    ]
  },
  id: "var1",
  name: "Extended Hard",
  priceOverride: {
    currency: "USD",
    amount: 100,
    localized: "100 USD"
  },
  quantity: 19,
  quantityAllocated: 12,
  stockQuantity: 1,
  product: {
    id: "prod1",
    name: "Our Awesome Book",
    thumbnailUrl: placeholderImage,
    images: {
      edges: [
        {
          node: {
            id: "img1",
            url: placeholderImage,
            alt: "Front",
            sortOrder: 1
          }
        },
        {
          node: {
            id: "img2",
            url: placeholderImage,
            alt: "Back",
            sortOrder: 4
          }
        },
        {
          node: {
            id: "img3",
            url: placeholderImage,
            alt: "Right side",
            sortOrder: 2
          }
        },
        {
          node: {
            id: "img4",
            url: placeholderImage,
            alt: "Left side",
            sortOrder: 3
          }
        },
        {
          node: {
            id: "img5",
            url: placeholderImage,
            alt: "Paper",
            sortOrder: 0
          }
        },
        {
          node: {
            id: "img6",
            url: placeholderImage,
            alt: "Hard cover",
            sortOrder: 1
          }
        },
        {
          node: {
            id: "img7",
            url: placeholderImage,
            alt: "Extended version",
            sortOrder: 0
          }
        },
        {
          node: {
            id: "img8",
            url: placeholderImage,
            alt: "Cut version",
            sortOrder: 2
          }
        },
        {
          node: {
            id: "img9",
            url: placeholderImage,
            alt: "Soft cover",
            sortOrder: 2
          }
        }
      ]
    },
    variants: {
      totalCount: 11,
      edges: [
        {
          node: {
            id: "var2",
            name: "Extended Soft"
          }
        },
        {
          node: {
            id: "var3",
            name: "Normal Hard"
          }
        },
        {
          node: {
            id: "var4",
            name: "Normal Soft"
          }
        }
      ]
    }
  },
  sku: "1230959124123",
  stock: 49,
  stockAllocated: 12
});
export const variantImages = (placeholderImage: string) =>
  variant(placeholderImage).images.edges.map(edge => edge.node);
export const variantProductImages = (placeholderImage: string) =>
  variant(placeholderImage).product.images.edges.map(edge => edge.node);
export const variantSiblings = (placeholderImage: string) =>
  variant(placeholderImage).product.variants.edges.map(edge => edge.node);
