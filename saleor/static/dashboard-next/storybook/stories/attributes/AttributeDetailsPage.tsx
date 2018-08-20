import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeDetailsPage from "../../../attributes/components/AttributeDetailsPage";
import { attributes } from "../../../attributes/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Attributes / Attribute details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <AttributeDetailsPage
      attribute={attributes[0]}
      disabled={false}
      saveButtonBarState="default"
      onBack={() => undefined}
      onDelete={undefined}
      onSubmit={() => undefined}
    />
  ))
  .add("when loading", () => (
    <AttributeDetailsPage
      disabled={true}
      saveButtonBarState="default"
      onBack={() => undefined}
      onDelete={undefined}
      onSubmit={() => undefined}
    />
  ))
  .add("when no values", () => (
    <AttributeDetailsPage
      attribute={{
        id: attributes[0].id,
        name: attributes[0].name,
        values: []
      }}
      disabled={false}
      saveButtonBarState="default"
      onBack={() => undefined}
      onDelete={undefined}
      onSubmit={() => undefined}
    />
  ));
