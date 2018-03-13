import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import { ProductList } from "../../category/components/ProductList";
import productListFixture from "./fixtures/productList";

describe("<ProductList />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ProductList
          loading={true}
          canLoadMore={false}
          handleLoadMore={jest.fn()}
          products={[]}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders properly when data is loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ProductList
          loading={false}
          canLoadMore={false}
          handleLoadMore={jest.fn()}
          products={productListFixture}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders properly 'load more' button", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ProductList
          loading={false}
          canLoadMore={true}
          handleLoadMore={jest.fn()}
          products={productListFixture}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders properly when product list is empty", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ProductList
          loading={false}
          canLoadMore={false}
          handleLoadMore={jest.fn()}
          products={[]}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
