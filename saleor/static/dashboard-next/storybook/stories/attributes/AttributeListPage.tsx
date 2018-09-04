import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeListPage from "../../../attributes/components/AttributeListPage";
import { attributes } from "../../../attributes/fixtures";
import { pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Attributes / Attribute list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <AttributeListPage attributes={attributes} {...pageListProps.default} />
  ))
  .add("loading", () => <AttributeListPage {...pageListProps.loading} />)
  .add("no data", () => (
    <AttributeListPage attributes={[]} {...pageListProps.default} />
  ));
