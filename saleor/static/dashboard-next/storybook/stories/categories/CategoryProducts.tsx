import { storiesOf } from "@storybook/react";
import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";

import CategoryProducts from "../../../category/components/CategoryProducts";

const products = [
  {
    id: "UHJvZHVjdDox",
    name: "Gardner, Graham and King",
    thumbnailUrl:
      "/media/__sized__/products/saleor/static/placeholders/t-shirts/6_tdo7a5D-crop-c0-5__0-5-255x255-70.jpg",
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoy",
    name: "Gardner, Graham and King",
    thumbnailUrl:
      "/media/__sized__/products/saleor/static/placeholders/t-shirts/6_tdo7a5D-crop-c0-5__0-5-255x255-70.jpg",
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoz",
    name: "Gardner, Graham and King",
    thumbnailUrl:
      "/media/__sized__/products/saleor/static/placeholders/t-shirts/6_tdo7a5D-crop-c0-5__0-5-255x255-70.jpg",
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  },
  {
    id: "UHJvZHVjdDoa",
    name: "Gardner, Graham and King",
    thumbnailUrl:
      "/media/__sized__/products/saleor/static/placeholders/t-shirts/6_tdo7a5D-crop-c0-5__0-5-255x255-70.jpg",
    productType: {
      id: "1",
      name: "T-Shirt"
    }
  }
];

storiesOf("Categories / CategoryProducts", module)
  .add("with initial data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      products={products}
      onCreate={() => {}}
      onFilter={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
    />
  ))
  .add("without initial data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      products={[]}
      onCreate={() => {}}
      onFilter={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
    />
  ))
  .add("when loading data", () => (
    <CategoryProducts
      hasNextPage={true}
      hasPreviousPage={false}
      onCreate={() => {}}
      onFilter={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
    />
  ));
