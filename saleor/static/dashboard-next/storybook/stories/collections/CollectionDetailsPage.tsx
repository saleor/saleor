import { storiesOf } from "@storybook/react";
import * as React from "react";

// FIXME: storyshots have problem with .jpg files, figure it out
// import * as placeholderImage from "../../../../placeholders/products-list/summer.jpg";
import * as placeholderImage from "../../../../images/placeholder540x540.png";
import { storefrontUrl } from "../../../collections";
import CollectionDetailsPage from "../../../collections/components/CollectionDetailsPage";
import { collections as collectionsFixture } from "../../../collections/fixtures";
import Decorator from "../../Decorator";

const collection = collectionsFixture(placeholderImage)[0];
const callbacks = {
  onBack: () => {},
  onDelete: () => {},
  onImageRemove: () => {},
  onShow: () => {},
  onSubmit: () => {},
  onNextPage: () => {},
  onPreviousPage: () => {},
  onProductAdd: () => {},
  onProductClick: () => () => {},
  onProductRemove: () => () => {},
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
