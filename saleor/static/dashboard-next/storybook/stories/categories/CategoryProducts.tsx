import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder60x60.png";
import CategoryProducts from "../../../categories/components/CategoryProducts";
import Decorator from "../../Decorator";

const products = [
  {
    id: "UHJvZHVjdDox",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholder,
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoy",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholder,
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoz",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholder,
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoa",
    name: "Gardner, Graham and King",
    thumbnailUrl: placeholder,
    productType: {
      id: "1",
      name: "T-Shirt"
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
      onAddProduct={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
    />
  ))
  .add("with initial data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      products={products}
      onAddProduct={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
    />
  ))
  .add("with clickable rows", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      products={products}
      onAddProduct={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onRowClick={() => () => {}}
    />
  ))
  .add("when loading data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      onAddProduct={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
    />
  ));
