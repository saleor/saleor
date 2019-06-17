import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeListPage, {
  AttributeListPageProps
} from "@saleor/attributes/components/AttributeListPage";
import { attributes } from "@saleor/attributes/fixtures";
import { listActionsProps, pageListProps } from "@saleor/fixtures";
import Decorator from "../../Decorator";

const props: AttributeListPageProps = {
  ...pageListProps.default,
  ...listActionsProps,
  attributes
};

storiesOf("Views / Attributes / Attribute list", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeListPage {...props} />)
  .add("loading", () => (
    <AttributeListPage {...props} attributes={undefined} disabled={true} />
  ))
  .add("no data", () => <AttributeListPage {...props} attributes={[]} />);
