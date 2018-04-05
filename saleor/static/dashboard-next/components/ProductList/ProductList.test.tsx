import * as React from "react";
import * as renderer from "react-test-renderer";

import ProductList from "./ProductList";

const products = [
  {
    id: "prod1",
    name: "Lewis PLC",
    productType: {
      id: "123412341234",
      name: "T-sirts"
    },
    thumbnailUrl:
      "/media/__sized__/products/saleor/static/placeholders/t-shirts/5_ZoF6Xi8-crop-c0-5__0-5-255x255-70.jpg"
  },
  {
    id: "prod2",
    name: "Kennedy-Ramirez",
    productType: {
      id: "123412341234",
      name: "T-sirts"
    },
    thumbnailUrl:
      "/media/__sized__/products/saleor/static/placeholders/t-shirts/6_07Fa6v8-crop-c0-5__0-5-255x255-70.jpg"
  },
  {
    id: "prod3",
    name: "Newman, Ashley and Roberson",
    productType: {
      id: "123412341234",
      name: "T-sirts"
    },
    thumbnailUrl:
      "/media/__sized__/products/saleor/static/placeholders/t-shirts/6_zeczDly-crop-c0-5__0-5-255x255-70.jpg"
  }
];

describe("<ProductList />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <ProductList
        hasPreviousPage={false}
        hasNextPage={false}
        onNextPage={jest.fn()}
        onPreviousPage={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders properly when data is loaded", () => {
    const component = renderer.create(
      <ProductList
        hasPreviousPage={false}
        hasNextPage={false}
        onNextPage={jest.fn()}
        onPreviousPage={jest.fn()}
        products={products}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders properly when product list is empty", () => {
    const component = renderer.create(
      <ProductList
        hasNextPage={false}
        onNextPage={jest.fn()}
        onPreviousPage={jest.fn()}
        products={[]}
      />
    );
    expect(component).toMatchSnapshot();
  });
});
