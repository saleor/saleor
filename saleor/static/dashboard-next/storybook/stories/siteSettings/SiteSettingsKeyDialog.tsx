import { storiesOf } from "@storybook/react";
import * as React from "react";

import SiteSettingsKeyDialog from "../../../siteSettings/components/SiteSettingsKeyDialog";
import Decorator from "../../Decorator";

storiesOf("SiteSettings / SiteSettingsKeyDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <SiteSettingsKeyDialog />)
  .add("other", () => <SiteSettingsKeyDialog />);
