import {
  ProductCreateData_productTypes_edges_node,
  ProductCreateData_productTypes_edges_node_productAttributes
} from "../products/types/ProductCreateData";
import { TaxRateType } from "../types/globalTypes";
import { ProductTypeDetails_productType } from "./types/ProductTypeDetails";
import { ProductTypeList_productTypes_edges_node } from "./types/ProductTypeList";

export const attributes: ProductCreateData_productTypes_edges_node_productAttributes[] = [
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTo5",
      name: "Author",
      slug: "author",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI0",
          name: "John Doe",
          slug: "john-doe",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI1",
          name: "Milionare Pirate",
          slug: "milionare-pirate",
          sortOrder: 1,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTo2",
      name: "Box Size",
      slug: "box-size",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE1",
          name: "100g",
          slug: "100g",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE2",
          name: "250g",
          slug: "250g",
          sortOrder: 1,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE3",
          name: "500g",
          slug: "500g",
          sortOrder: 2,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE4",
          name: "1kg",
          slug: "1kg",
          sortOrder: 3,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZToz",
      name: "Brand",
      slug: "brand",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjY=",
          name: "Saleor",
          slug: "saleor",
          sortOrder: 0,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTo4",
      name: "Candy Box Size",
      slug: "candy-box-size",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjIx",
          name: "100g",
          slug: "100g",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjIy",
          name: "250g",
          slug: "250g",
          sortOrder: 1,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjIz",
          name: "500g",
          slug: "500g",
          sortOrder: 2,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTo1",
      name: "Coffee Genre",
      slug: "coffee-genre",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjEz",
          name: "Arabica",
          slug: "arabica",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE0",
          name: "Robusta",
          slug: "robusta",
          sortOrder: 1,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZToy",
      name: "Collar",
      slug: "collar",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjM=",
          name: "Round",
          slug: "round",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjQ=",
          name: "V-Neck",
          slug: "v-neck",
          sortOrder: 1,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjU=",
          name: "Polo",
          slug: "polo",
          sortOrder: 2,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTox",
      name: "Color",
      slug: "color",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE=",
          name: "Blue",
          slug: "blue",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI=",
          name: "White",
          slug: "white",
          sortOrder: 1,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZToxMg==",
      name: "Cover",
      slug: "cover",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjMw",
          name: "Soft",
          slug: "soft",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjMx",
          name: "Hard",
          slug: "hard",
          sortOrder: 1,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjMy",
          name: "Middle soft",
          slug: "middle-soft",
          sortOrder: 2,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjMz",
          name: "Middle hard",
          slug: "middle-hard",
          sortOrder: 3,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjM0",
          name: "Middle",
          slug: "middle",
          sortOrder: 4,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjM1",
          name: "Very hard",
          slug: "very-hard",
          sortOrder: 5,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTo3",
      name: "Flavor",
      slug: "flavor",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE5",
          name: "Sour",
          slug: "sour",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjIw",
          name: "Sweet",
          slug: "sweet",
          sortOrder: 1,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZToxMQ==",
      name: "Language",
      slug: "language",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI4",
          name: "English",
          slug: "english",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI5",
          name: "Pirate",
          slug: "pirate",
          sortOrder: 1,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZToxMA==",
      name: "Publisher",
      slug: "publisher",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI2",
          name: "Mirumee Press",
          slug: "mirumee-press",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI3",
          name: "Saleor Publishing",
          slug: "saleor-publishing",
          sortOrder: 1,
          type: "STRING",
          value: ""
        }
      ]
    }
  },
  {
    node: {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTo0",
      name: "Size",
      slug: "size",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjc=",
          name: "XS",
          slug: "xs",
          sortOrder: 0,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjg=",
          name: "S",
          slug: "s",
          sortOrder: 1,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjk=",
          name: "M",
          slug: "m",
          sortOrder: 2,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjEw",
          name: "L",
          slug: "l",
          sortOrder: 3,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjEx",
          name: "XL",
          slug: "xl",
          sortOrder: 4,
          type: "STRING",
          value: ""
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjEy",
          name: "XXL",
          slug: "xxl",
          sortOrder: 5,
          type: "STRING",
          value: ""
        }
      ]
    }
  }
].map(edge => edge.node);

export const productTypes: Array<
  ProductCreateData_productTypes_edges_node &
    ProductTypeList_productTypes_edges_node
> = [
  {
    __typename: "ProductType" as "ProductType",
    hasVariants: true,
    id: "UHJvZHVjdFR5cGU6NA==",
    isShippingRequired: true,
    name: "Candy",
    productAttributes: [attributes[0]],
    taxRate: "FOODSTUFFS" as TaxRateType,
    variantAttributes: [attributes[1], attributes[2]]
  },
  {
    __typename: "ProductType" as "ProductType",
    hasVariants: false,
    id: "UHJvZHVjdFR5cGU6NQ==",
    isShippingRequired: false,
    name: "E-books",
    productAttributes: [attributes[5]],
    taxRate: "STANDARD" as TaxRateType,
    variantAttributes: [attributes[0], attributes[3]]
  },
  {
    __typename: "ProductType" as "ProductType",
    hasVariants: false,
    id: "UHJvZHVjdFR5cGU6Mg==",
    isShippingRequired: true,
    name: "Mugs",
    productAttributes: [attributes[7]],
    taxRate: "STANDARD" as TaxRateType,
    variantAttributes: [attributes[2], attributes[5]]
  },
  {
    __typename: "ProductType" as "ProductType",
    hasVariants: true,
    id: "UHJvZHVjdFR5cGU6Mw==",
    isShippingRequired: true,
    name: "Coffee",
    productAttributes: [attributes[8]],
    taxRate: "STANDARD" as TaxRateType,
    variantAttributes: [attributes[1], attributes[4]]
  },
  {
    __typename: "ProductType" as "ProductType",
    hasVariants: true,
    id: "UHJvZHVjdFR5cGU6MQ==",
    isShippingRequired: true,
    name: "T-Shirt",
    productAttributes: [attributes[4]],
    taxRate: "STANDARD" as TaxRateType,
    variantAttributes: [attributes[1], attributes[6]]
  }
].map(productType => ({
  __typename: "ProductType" as "ProductType",
  ...productType
}));
export const productType: ProductTypeDetails_productType = {
  __typename: "ProductType" as "ProductType",
  hasVariants: false,
  id: "UHJvZHVjdFR5cGU6NQ==",
  isShippingRequired: false,
  name: "E-books",
  productAttributes: [
    {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZTo5",
      name: "Author",
      slug: "author",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI0",
          name: "John Doe",
          slug: "john-doe"
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI1",
          name: "Milionare Pirate",
          slug: "milionare-pirate"
        }
      ]
    },
    {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZToxMQ==",
      name: "Language",
      slug: "language",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI4",
          name: "English",
          slug: "english"
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI5",
          name: "Pirate",
          slug: "pirate"
        }
      ]
    },
    {
      __typename: "Attribute" as "Attribute",
      id: "UHJvZHVjdEF0dHJpYnV0ZToxMA==",
      name: "Publisher",
      slug: "publisher",
      values: [
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI2",
          name: "Mirumee Press",
          slug: "mirumee-press"
        },
        {
          __typename: "AttributeValue" as "AttributeValue",
          id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI3",
          name: "Saleor Publishing",
          slug: "saleor-publishing"
        }
      ]
    }
  ],
  taxRate: "STANDARD" as TaxRateType,
  variantAttributes: [],
  weight: {
    __typename: "Weight",
    unit: "kg",
    value: 7.82
  }
};
