import { storiesOf } from "@storybook/react";
import React from "react";

import placeholder from "../../../../images/placeholder60x60.png";
import CategoryProducts from "../../../categories/components/CategoryProducts";
import Decorator from "../../Decorator";

const products = [
  {
    id: "UHJvZHVjdDox",
    name: "Gardner, Graham and King",
    productType: {
      id: "1",
      name: "T-Shirt"
    },
    thumbnail: {
      url: placeholder
    }
  },
  {
    id: "UHJvZHVjdDoy",
    name: "Gardner, Graham and King",
    productType: {
      id: "1",
      name: "T-Shirt"
    },
    thumbnail: {
      url: placeholder
    }
  },
  {
    id: "UHJvZHVjdDoz",
    name: "Gardner, Graham and King",
    productType: {
      id: "1",
      name: "T-Shirt"
    },
    thumbnail: {
      url: placeholder
    }
  },
  {
    id: "UHJvZHVjdDoa",
    name: "Gardner, Graham and King",
    productType: {
      id: "1",
      name: "T-Shirt"
    },
    thumbnail: {
      url: placeholder
    }
  }
];

storiesOf("Categories / CategoryProducts", module)
  .addDecorator(Decorator)
  .add("without initial data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      products={[]}
      onAddProduct={undefined}
      onNextPage={undefined}
      onPreviousPage={undefined}
    />
  ))
  .add("with initial data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      products={products}
      onAddProduct={undefined}
      onNextPage={undefined}
      onPreviousPage={undefined}
    />
  ))
  .add("with clickable rows", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      products={products}
      onAddProduct={undefined}
      onNextPage={undefined}
      onPreviousPage={undefined}
      onRowClick={() => undefined}
    />
  ))
  .add("when loading data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      onAddProduct={undefined}
      onNextPage={undefined}
      onPreviousPage={undefined}
    />
  ));
