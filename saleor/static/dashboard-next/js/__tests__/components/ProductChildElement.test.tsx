import * as React from "react";
import { MemoryRouter } from "react-router-dom";
import * as renderer from "react-test-renderer";

import { ProductChildElement } from "../../category/components/ProductChildElement";
import productFixture from "./fixtures/product";

describe("<ProductChildElement />", () => {
  it("renders while data is loading", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ProductChildElement
          label=""
          url=""
          thumbnail=""
          price=""
          loading={true}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when data is loaded", () => {
    const component = renderer.create(
      <MemoryRouter>
        <ProductChildElement
          label={productFixture.node.name}
          url={`/products/${productFixture.node.id}/`}
          thumbnail={productFixture.node.thumbnailUrl}
          price={productFixture.node.price.localized}
          loading={false}
        />
      </MemoryRouter>
    );
    expect(component).toMatchSnapshot();
  });
});
