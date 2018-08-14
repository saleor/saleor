import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder1080x1080.png";
import ProductImagePage from "../../../products/components/ProductImagePage";
import Decorator from "../../Decorator";

const image = { id: "", url: placeholder };
const images = (Array(8) as any)
  .fill({ id: "img", url: placeholder })
  .map((image, imageIndex) => ({ ...image, id: image.id + imageIndex }));

storiesOf("Views / Products / Product image details", module)
  .addDecorator(Decorator)
  .add("when loaded data", () => (
    <ProductImagePage
      description={"Lorem ipsum"}
      disabled={false}
      image={image}
      images={images}
      onBack={() => {}}
      onDelete={() => {}}
      onRowClick={() => () => {}}
      onSubmit={() => {}}
    />
  ))
  .add("when loading data", () => (
    <ProductImagePage
      disabled={true}
      onBack={() => {}}
      onDelete={() => {}}
      onRowClick={() => () => {}}
      onSubmit={() => {}}
    />
  ));
