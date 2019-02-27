import { content } from "../storybook/stories/components/RichTextEditor";
import { CategoryDetails_category } from "./types/CategoryDetails";

export const categories = [
  {
    children: {
      totalCount: 2
    },
    id: "123123",
    name: "Lorem ipsum dolor",
    products: {
      totalCount: 4
    }
  },
  {
    children: {
      totalCount: 54
    },
    id: "876752",
    name: "Mauris vehicula tortor vulputate",
    products: {
      totalCount: 3
    }
  },
  {
    children: {
      totalCount: 2
    },
    id: "876542",
    name: "Excepteur sint occaecat cupidatat non proident",
    products: {
      totalCount: 6
    }
  },
  {
    children: {
      totalCount: 6
    },
    id: "875352",
    name: "Ut enim ad minim veniam",
    products: {
      totalCount: 12
    }
  },
  {
    children: {
      totalCount: 76
    },
    id: "865752",
    name: "Duis aute irure dolor in reprehenderit",
    products: {
      totalCount: 43
    }
  },
  {
    children: {
      totalCount: 11
    },
    id: "878752",
    name: "Neque porro quisquam est",
    products: {
      totalCount: 21
    }
  }
];
export const category: (
  placeholderImage: string
) => CategoryDetails_category = (placeholderImage: string) => ({
  __typename: "Category",
  backgroundImage: {
    __typename: "Image",
    alt: "Alt text",
    url: placeholderImage
  },
  children: {
    __typename: "CategoryCountableConnection",
    edges: []
  },
  descriptionJson: JSON.stringify(content),
  id: "Q2F0ZWdvcnk6NA==",
  name: "Coffees",
  parent: {
    __typename: "Category",
    id: "Q2F0ZWdvcnk6Mw=="
  },
  products: {
    __typename: "ProductCountableConnection",
    edges: [
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjA=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyMQ==",
          name: "Gardner-Schultz",
          price: {
            __typename: "Money",
            amount: 83.3,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjE=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyMg==",
          name: "James, Martinez and Murray",
          price: {
            __typename: "Money",
            amount: 68.27,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjI=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyMw==",
          name: "Curtis, Joyce and Turner",
          price: {
            __typename: "Money",
            amount: 21.43,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjM=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyNA==",
          name: "Davis, Brown and Ray",
          price: {
            __typename: "Money",
            amount: 62.76,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjQ=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyNQ==",
          name: "Gallegos Ltd",
          price: {
            __typename: "Money",
            amount: 7.13,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjU=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyNg==",
          name: "Franklin Inc",
          price: {
            __typename: "Money",
            amount: 48.82,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjY=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyNw==",
          name: "Williams-Taylor",
          price: {
            __typename: "Money",
            amount: 27.34,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjc=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyOA==",
          name: "Riddle, Evans and Hicks",
          price: {
            __typename: "Money",
            amount: 75.42,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjg=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDoyOQ==",
          name: "Hebert-Sherman",
          price: {
            __typename: "Money",
            amount: 86.62,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      },
      {
        __typename: "ProductCountableEdge",
        cursor: "YXJyYXljb25uZWN0aW9uOjk=",
        node: {
          __typename: "Product",
          availability: {
            __typename: "ProductAvailability",
            available: true
          },
          id: "UHJvZHVjdDozMA==",
          name: "Carter and Sons",
          price: {
            __typename: "Money",
            amount: 48.66,
            currency: "USD"
          },
          productType: {
            __typename: "ProductType",
            id: "UHJvZHVjdFR5cGU6Mw==",
            name: "Coffee"
          },
          thumbnail: { __typename: "Image", url: placeholderImage }
        }
      }
    ],
    pageInfo: {
      __typename: "PageInfo",
      endCursor: "YXJyYXljb25uZWN0aW9uOjk=",
      hasNextPage: false,
      hasPreviousPage: false,
      startCursor: "YXJyYXljb25uZWN0aW9uOjA="
    }
  },
  seoDescription: null,
  seoTitle: null
});
export const errors = [
  {
    field: "name",
    message: "To pole jest wymagane."
  }
];
