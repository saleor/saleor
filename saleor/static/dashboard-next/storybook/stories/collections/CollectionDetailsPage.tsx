import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../placeholders/products-list/summer.jpg";
import CollectionDetailsPage from "../../../collections/components/CollectionDetailsPage";
import { collections as collectionsFixture } from "../../../collections/fixtures";
import { storefrontUrl } from "../../../collections";
import Decorator from "../../Decorator";

const collection = collectionsFixture(placeholderImage)[0];
const callbacks = {
  onBack: () => {},
  storefrontUrl
};

storiesOf("Views / Collections / Collection details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CollectionDetailsPage
      collection={collection}
      products={collection.products.edges.map(edge => edge.node)}
      {...callbacks}
    />
  ))
  .add("other", () => <CollectionDetailsPage disabled={true} {...callbacks} />);
