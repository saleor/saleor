import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductUpdatePage from "../../../products/components/ProductUpdatePage";

const product = {
  id: "1231u",
  description:
    "Aenean sit amet malesuada nibh. Proin nisi lorem, facilisis at tortor vel, convallis ornare nibh. In nec ipsum porta, varius leo eu, condimentum quam. Donec gravida euismod ipsum, at consequat orci efficitur nec. Phasellus lectus arcu, auctor eget porttitor eget, venenatis a lacus. Suspendisse quis urna rhoncus, commodo justo at, tempor nisl.",
  name: "Our awesome book",
  price: {
    currencySymbol: "$",
    net: 3000.1
  },
  available: true,
  availableOn: "23-01-2006",
  seo: {
    title: "Buy our awesome book now!",
    description: "Order our awesome book right now!"
  },
  category: {
    id: "123123"
  },
  slug: "our-awesome-book-1231u",
  attributes: [
    {
      name: "brand",
      value: "superbrand"
    },
    {
      name: "collar",
      value: "round"
    },
    {
      name: "color",
      value: "blue"
    }
  ],
  collections: { edges: [{ node: { id: "1", name: "Winter collection" } }] },
  productType: {
    name: "Book",
    productAttributes: {
      edges: [
        {
          node: {
            id: "UHJvZHVjdEF0dHJpYnV0ZToz",
            slug: "brand",
            name: "Brand",
            values: [
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjQw",
                name: "dominikibrand",
                slug: "dominikibrand"
              },
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjM5",
                name: "superbrand",
                slug: "superbrand"
              },
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjM4",
                name: "Mirumee",
                slug: "mirumee"
              },
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjY=",
                name: "Saleor",
                slug: "saleor"
              }
            ]
          }
        },
        {
          node: {
            id: "UHJvZHVjdEF0dHJpYnV0ZToy",
            slug: "collar",
            name: "Collar",
            values: [
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjU=",
                name: "Polo",
                slug: "polo"
              },
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjQ=",
                name: "V-Neck",
                slug: "v-neck"
              },
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjM=",
                name: "Round",
                slug: "round"
              }
            ]
          }
        },
        {
          node: {
            id: "UHJvZHVjdEF0dHJpYnV0ZTox",
            slug: "color",
            name: "Color",
            values: [
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjI=",
                name: "White",
                slug: "white"
              },
              {
                id: "UHJvZHVjdEF0dHJpYnV0ZVZhbHVlOjE=",
                name: "Blue",
                slug: "blue"
              }
            ]
          }
        }
      ]
    }
  }
};
const collections = [
  { id: "1", name: "Winter collection" },
  { id: "2", name: "Emperor's choice" }
];
const categories = [
  {
    id: "123123",
    name: "Lorem ipsum dolor"
  },
  {
    id: "876752",
    name: "Mauris vehicula tortor vulputate"
  }
];

storiesOf("Products / ProductUpdatePage", module)
  .add("when loading data", () => (
    <ProductUpdatePage onBack={() => {}} onSubmit={() => {}} loading={true} />
  ))
  .add("when data is fully loaded", () => (
    <ProductUpdatePage
      onBack={() => {}}
      onSubmit={() => {}}
      product={product}
      collections={collections}
      categories={categories}
    />
  ));
