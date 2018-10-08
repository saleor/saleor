import { storiesOf } from "@storybook/react";
import * as React from "react";

import SiteSettingsPage, {
  SiteSettingsPageProps
} from "../../../siteSettings/components/SiteSettingsPage";
import { shop } from "../../../siteSettings/fixtures";
import Decorator from "../../Decorator";

const props: SiteSettingsPageProps = {
  disabled: false,
  onSubmit: () => undefined,
  shop
};

storiesOf("Views / Site settings / Page", module)
  .addDecorator(Decorator)
  .add("default", () => <SiteSettingsPage {...props} />)
  .add("loading", () => <SiteSettingsPage {...props} disabled={true} />);
