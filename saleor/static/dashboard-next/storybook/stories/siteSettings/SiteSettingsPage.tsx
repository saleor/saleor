import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import SiteSettingsPage, {
  SiteSettingsPageProps
} from "../../../siteSettings/components/SiteSettingsPage";
import { shop } from "../../../siteSettings/fixtures";
import Decorator from "../../Decorator";
import { formError } from "../../misc";

const props: Omit<SiteSettingsPageProps, "classes"> = {
  disabled: false,
  errors: [],
  onBack: () => undefined,
  onKeyAdd: () => undefined,
  onKeyRemove: () => undefined,
  onSubmit: () => undefined,
  saveButtonBarState: "default",
  shop
};

storiesOf("Views / Site settings / Page", module)
  .addDecorator(Decorator)
  .add("default", () => <SiteSettingsPage {...props} />)
  .add("loading", () => (
    <SiteSettingsPage {...props} disabled={true} shop={undefined} />
  ))
  .add("form errors", () => (
    <SiteSettingsPage
      {...props}
      errors={["description", "domain", "name"].map(field => formError(field))}
    />
  ));
