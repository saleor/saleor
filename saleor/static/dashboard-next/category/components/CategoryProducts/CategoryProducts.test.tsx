import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import CategoryProducts from "./CategoryProducts";

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

describe("<CategoryProducts />", () => {
  it("renders with initial data", () => {
    const component = renderer.create(
      <CategoryProducts
        hasNextPage={true}
        hasPreviousPage={false}
        products={products}
        onCreate={jest.fn()}
        onFilter={jest.fn()}
        onNextPage={jest.fn()}
        onPreviousPage={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders without initial data", () => {
    const component = renderer.create(
      <CategoryProducts
        hasNextPage={true}
        hasPreviousPage={false}
        products={[]}
        onCreate={jest.fn()}
        onFilter={jest.fn()}
        onNextPage={jest.fn()}
        onPreviousPage={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when loading data", () => {
    const component = renderer.create(
      <CategoryProducts
        hasNextPage={true}
        hasPreviousPage={false}
        onCreate={jest.fn()}
        onFilter={jest.fn()}
        onNextPage={jest.fn()}
        onPreviousPage={jest.fn()}
      />
    );
    expect(component).toMatchSnapshot();
  });
});
