import { storiesOf } from "@storybook/react";
import * as React from "react";

import { attribute } from "@saleor/attributes/fixtures";
import AttributePage, {
  AttributePageProps
} from "../../../attributes/components/AttributePage";
import Decorator from "../../Decorator";

const props: AttributePageProps = {
  attribute,
  disabled: false,
  onBack: () => undefined,
  onDelete: () => undefined,
  onSubmit: () => undefined,
  onValueAdd: () => undefined,
  onValueDelete: () => undefined,
  onValueUpdate: () => undefined,
  saveButtonBarState: "default",
  values: attribute.values
};

storiesOf("Views / Attributes / Attribute details", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributePage {...props} />)
  .add("loading", () => (
    <AttributePage
      {...props}
      attribute={undefined}
      disabled={true}
      values={undefined}
    />
  ))
  .add("no values", () => <AttributePage {...props} values={undefined} />)
  .add("create", () => <AttributePage {...props} attribute={null} />);
