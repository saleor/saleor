import { storiesOf } from "@storybook/react";
import * as React from "react";

import { configurationMenu } from "../../../configuration";
import ConfigurationPage, {
  ConfigurationPageProps
} from "../../../configuration/ConfigurationPage";
import { staffMember } from "../../../staff/fixtures";
import Decorator from "../../Decorator";

const user = {
  __typename: staffMember.__typename,
  email: staffMember.email,
  id: staffMember.id,
  isStaff: true,
  note: null,
  permissions: staffMember.permissions
};
const props: ConfigurationPageProps = {
  menu: configurationMenu,
  onSectionClick: () => undefined,
  user
};
const partialAccessProps: ConfigurationPageProps = {
  ...props,
  user: {
    ...user,
    permissions: user.permissions.slice(2, 6)
  }
};

storiesOf("Views / Configuration", module)
  .addDecorator(Decorator)
  .add("default", () => <ConfigurationPage {...props} />)
  .add("partial access", () => <ConfigurationPage {...partialAccessProps} />);
