import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductAttributesForm from "../../../products/components/ProductAttributesForm";

const productAttributes = [
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
];
const attributes = [
  {
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
  },
  {
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
  },
  {
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
];

storiesOf("Products / ProductAttributesForm", module)
  .add("when loading data", () => (
    <ProductAttributesForm loading={true} onChange={() => {}} />
  ))
  .add("when data loaded", () => (
    <ProductAttributesForm
      attributes={attributes}
      productAttributes={productAttributes}
      onChange={() => {}}
    />
  ));
