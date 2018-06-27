import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionListPage from "../../../collections/components/CollectionListPage";
import { collections as collectionsFixture } from "../../../collections/fixtures";
import { pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";

const collections = collectionsFixture("");

storiesOf("Views / Collections / Collection list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CollectionListPage collections={collections} {...pageListProps.default} />
  ))
  .add("when loading", () => <CollectionListPage {...pageListProps.loading} />);
