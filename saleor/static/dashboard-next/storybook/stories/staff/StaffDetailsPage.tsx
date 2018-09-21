import { storiesOf } from "@storybook/react";
import * as React from "react";

import StaffDetailsPage, {
  StaffDetailsPageProps
} from "../../../staff/components/StaffDetailsPage";
import { staffMember } from "../../../staff/fixtures";
import Decorator from "../../Decorator";

const props: StaffDetailsPageProps = {
  disabled: false,
  onBack: () => undefined,
  onDelete: () => undefined,
  onSubmit: () => undefined,
  staffMember
};

storiesOf("Views / Staff / Staff member details", module)
  .addDecorator(Decorator)
  .add("default", () => <StaffDetailsPage {...props} />)
  .add("loading", () => (
    <StaffDetailsPage {...props} disabled={true} staffMember={undefined} />
  ));
