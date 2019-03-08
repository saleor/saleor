import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder1080x1080.png";
import ProductImagePage from "../../../products/components/ProductImagePage";
import Decorator from "../../Decorator";

const image = { id: "", url: placeholder, alt: "Lorem ipsum" };
const images = (Array(8) as any)
  .fill({ id: "img", url: placeholder })
  .map((image, imageIndex) => ({ ...image, id: image.id + imageIndex }));

storiesOf("Views / Products / Product image details", module)
  .addDecorator(Decorator)
  .add("when loaded data", () => (
    <ProductImagePage
      product="Example product"
      disabled={false}
      image={image}
      images={images}
      onBack={() => undefined}
      onDelete={undefined}
      onRowClick={() => undefined}
      onSubmit={() => undefined}
      saveButtonBarState="default"
    />
  ))
  .add("when loading data", () => (
    <ProductImagePage
      product="Example product"
      disabled={true}
      onBack={() => undefined}
      onDelete={undefined}
      onRowClick={() => undefined}
      onSubmit={() => undefined}
      saveButtonBarState="default"
    />
  ));
