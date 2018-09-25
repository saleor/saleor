import { TaxRateType } from "../types/globalTypes";
import { ProductTypeDetails_productType } from "./types/ProductTypeDetails";
import { ProductTypeList_productTypes_edges_node } from "./types/ProductTypeList";

export const productTypes: ProductTypeList_productTypes_edges_node[] = [
  {
    __typename: "ProductType",
    hasVariants: true,
    id: "UHJvZHVjdFR5cGU6NA==",
    isShippingRequired: true,
    name: "Candy",
    taxRate: "FOODSTUFFS" as TaxRateType
  },
  {
    __typename: "ProductType",
    hasVariants: false,
    id: "UHJvZHVjdFR5cGU6NQ==",
    isShippingRequired: false,
    name: "E-books",
    taxRate: "STANDARD" as TaxRateType
  },
  {
    __typename: "ProductType",
    hasVariants: false,
    id: "UHJvZHVjdFR5cGU6Mg==",
    isShippingRequired: true,
    name: "Mugs",
    taxRate: "STANDARD" as TaxRateType
  },
  {
    __typename: "ProductType",
    hasVariants: true,
    id: "UHJvZHVjdFR5cGU6Mw==",
    isShippingRequired: true,
    name: "Coffee",
    taxRate: "STANDARD" as TaxRateType
  },
  {
    __typename: "ProductType",
    hasVariants: true,
    id: "UHJvZHVjdFR5cGU6MQ==",
    isShippingRequired: true,
    name: "T-Shirt",
    taxRate: "STANDARD" as TaxRateType
  }
].map(productType => ({
  ...productType,
  __typename: "ProductType" as "ProductType"
}));
export const productType: ProductTypeDetails_productType = {
  hasVariants: true,
  id: "pt77249",
  isShippingRequired: true,
  name: "Cotton",
  productAttributes: [
    {
      id: "pta27565",
      name: "Virginia",
      slug: "Virginia",
      sortNumber: 0
    },
    {
      id: "pta84650",
      name: "Tasty Granite Table",
      slug: "Tasty-Granite-Table",
      sortNumber: 1
    },
    { id: "pta50103", sortNumber: 2, name: "Small", slug: "Small" }
  ].map(attribute => ({
    ...attribute,
    __typename: "Attribute" as "Attribute"
  })),
  taxRate: TaxRateType.ACCOMMODATION,
  variantAttributes: [
    {
      id: "pta24175",
      name: "enhance",
      slug: "enhance",
      sortNumber: 4
    },
    {
      id: "pta66068",
      name: "Djibouti Franc",
      slug: "Djibouti-Franc",
      sortNumber: 5
    }
  ].map(attribute => ({ ...attribute, __typename: "Attribute" as "Attribute" }))
};
export const attributes = [
  { id: "pta27565", sortNumber: 0, name: "Virginia", slug: "Virginia" },
  {
    id: "pta84650",
    name: "Tasty Granite Table",
    slug: "Tasty-Granite-Table",
    sortNumber: 1
  },
  { id: "pta50103", sortNumber: 2, name: "Small", slug: "Small" },
  {
    id: "pta95599",
    name: "Home Loan Account",
    slug: "Home-Loan-Account",
    sortNumber: 3
  },
  { id: "pta24175", sortNumber: 4, name: "enhance", slug: "enhance" },
  {
    id: "pta66068",
    name: "Djibouti Franc",
    slug: "Djibouti-Franc",
    sortNumber: 5
  },
  { id: "pta41930", sortNumber: 6, name: "Rustic", slug: "Rustic" },
  { id: "pta91235", sortNumber: 7, name: "Principal", slug: "Principal" },
  { id: "pta50181", sortNumber: 8, name: "Outdoors", slug: "Outdoors" },
  { id: "pta38700", sortNumber: 9, name: "Canada", slug: "Canada" }
];
