import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../placeholders/products-list/summer.jpg";
import { storefrontUrl } from "../../../collections";
import CollectionDetailsPage from "../../../collections/components/CollectionDetailsPage";
import { collections as collectionsFixture } from "../../../collections/fixtures";
import Decorator from "../../Decorator";

const collection = collectionsFixture(placeholderImage)[0];
const callbacks = {
  onBack: undefined,
  onDelete: undefined,
  onImageRemove: undefined,
  onNextPage: undefined,
  onPreviousPage: undefined,
  onProductAdd: undefined,
  onProductClick: () => undefined,
  onProductRemove: () => undefined,
  onShow: undefined,
  onSubmit: () => undefined,
  storefrontUrl
};

storiesOf("Views / Collections / Collection details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CollectionDetailsPage
      disabled={false}
      collection={collection}
      products={collection.products.edges.map(edge => edge.node)}
      {...callbacks}
    />
  ))
  .add("when loading", () => (
    <CollectionDetailsPage disabled={true} {...callbacks} />
  ));
