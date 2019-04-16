import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderCollectionImage from "../../../../images/block1.jpg";
import * as placeholderProductImage from "../../../../images/placeholder60x60.png";
import CollectionDetailsPage, {
  CollectionDetailsPageProps
} from "../../../collections/components/CollectionDetailsPage";
import { collection as collectionFixture } from "../../../collections/fixtures";
import { listActionsProps, pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";

const collection = collectionFixture(
  placeholderCollectionImage,
  placeholderProductImage
);

const props: Omit<CollectionDetailsPageProps, "classes"> = {
  ...listActionsProps,
  ...pageListProps.default,
  collection,
  disabled: false,
  isFeatured: true,
  onBack: () => undefined,
  onCollectionRemove: () => undefined,
  onImageDelete: () => undefined,
  onImageUpload: () => undefined,
  onProductUnassign: () => undefined,
  onSubmit: () => undefined,
  saveButtonBarState: "default"
};

storiesOf("Views / Collections / Collection details", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionDetailsPage {...props} />)
  .add("loading", () => (
    <CollectionDetailsPage {...props} collection={undefined} disabled={true} />
  ))
  .add("no products", () => (
    <CollectionDetailsPage
      {...props}
      collection={{
        ...collection,
        products: {
          ...collection.products,
          edges: []
        }
      }}
      disabled={true}
    />
  ));
