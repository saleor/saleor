import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionCreatePage, {
  CollectionCreatePageProps
} from "../../../collections/components/CollectionCreatePage";
import Decorator from "../../Decorator";

const props: CollectionCreatePageProps = {
  disabled: false,
  errors: [],
  onBack: () => undefined,
  onSubmit: () => undefined
};

storiesOf("Views / Collections / Create collection", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionCreatePage {...props} />)
  .add("loading", () => <CollectionCreatePage {...props} disabled={true} />);
