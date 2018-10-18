import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import CollectionDetailsPage, {
  CollectionDetailsPageProps
} from "../../../collections/components/CollectionDetailsPage";
import { collection as collectionFixture } from "../../../collections/fixtures";
import Decorator from "../../Decorator";

const collection = collectionFixture(placeholderImage);

const props: CollectionDetailsPageProps = {
  collection,
  onBack: () => undefined,
  onCollectionRemove: () => undefined,
  onImageUpload: () => undefined,
  onSubmit: () => undefined
};

storiesOf("Views / Collections / Collection details", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionDetailsPage {...props} />)
  .add("other", () => (
    <CollectionDetailsPage {...props} collection={undefined} />
  ));
