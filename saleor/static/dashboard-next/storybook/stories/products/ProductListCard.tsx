import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder255x255.png";
import ProductListCard from "../../../products/components/ProductListCard";
import { pageListProps } from "../../../fixtures";

const images = [
  {
    id: "2",
    alt: "Image 2",
    url: placeholder as string,
    order: 2
  },
  {
    id: "1",
    alt: "Image 1",
    url: placeholder as string,
    order: 1
  }
];

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

storiesOf("Views / Products / Product list", module)
  .add("default", () => (
    <ProductListCard products={products} {...pageListProps.default} />
  ))
  .add("loading", () => <ProductListCard {...pageListProps.loading} />)
  .add("no data", () => (
    <ProductListCard products={[]} {...pageListProps.default} />
  ));
