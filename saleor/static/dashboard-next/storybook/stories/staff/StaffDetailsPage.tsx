import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import StaffDetailsPage, {
  StaffDetailsPageProps
} from "../../../staff/components/StaffDetailsPage";
import { permissions, staffMember } from "../../../staff/fixtures";
import Decorator from "../../Decorator";

const props: Omit<StaffDetailsPageProps, "classes"> = {
  canEditStatus: true,
  canRemove: true,
  disabled: false,
  onBack: () => undefined,
  onDelete: () => undefined,
  onSubmit: () => undefined,
  permissions,
  saveButtonBarState: "default",
  staffMember
};

storiesOf("Views / Staff / Staff member details", module)
  .addDecorator(Decorator)
  .add("default", () => <StaffDetailsPage {...props} />)
  .add("loading", () => (
    <StaffDetailsPage {...props} disabled={true} staffMember={undefined} />
  ))
  .add("not admin", () => (
    <StaffDetailsPage
      {...props}
      staffMember={{
        ...staffMember,
        permissions: staffMember.permissions.slice(1)
      }}
    />
  ))
  .add("himself", () => (
    <StaffDetailsPage {...props} canEditStatus={false} canRemove={false} />
  ));
