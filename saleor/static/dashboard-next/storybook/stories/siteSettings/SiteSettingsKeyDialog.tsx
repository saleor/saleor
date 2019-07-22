import { storiesOf } from "@storybook/react";
import React from "react";

import SiteSettingsKeyDialog, {
  SiteSettingsKeyDialogProps
} from "../../../siteSettings/components/SiteSettingsKeyDialog";
import { AuthorizationKeyType } from "../../../types/globalTypes";
import Decorator from "../../Decorator";
import { formError } from "../../misc";

const props: SiteSettingsKeyDialogProps = {
  errors: [],
  initial: {
    key: "912n3n123j9",
    password: "090das9d86gad678adf7ad6f88asd8",
    type: AuthorizationKeyType.FACEBOOK
  },
  onClose: () => undefined,
  open: true
};

storiesOf("SiteSettings / Add key dialog", module)
  .addDecorator(Decorator)
  .add("default", () => <SiteSettingsKeyDialog {...props} />)
  .add("form errors", () => (
    <SiteSettingsKeyDialog
      {...props}
      errors={["key", "password", "keyType"].map(field => formError(field))}
    />
  ));
