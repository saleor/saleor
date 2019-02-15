import { storiesOf } from "@storybook/react";
import * as React from "react";

import SaleCreatePage, {
  SaleCreatePageProps
} from "../../../discounts/components/SaleCreatePage";
import Decorator from "../../Decorator";
import { formError } from "../../misc";

const props: SaleCreatePageProps = {
  defaultCurrency: "USD",
  disabled: false,
  errors: [],
  onBack: () => undefined,
  onSubmit: () => undefined,
  saveButtonBarState: "default"
};

storiesOf("Views / Discounts / Sale create", module)
  .addDecorator(Decorator)
  .add("default", () => <SaleCreatePage {...props} />)
  .add("loading", () => <SaleCreatePage {...props} disabled={true} />)
  .add("form errors", () => (
    <SaleCreatePage
      {...props}
      errors={["name", "startDate", "endDate", "value"].map(formError)}
    />
  ));
