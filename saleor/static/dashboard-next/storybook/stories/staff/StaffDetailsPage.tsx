import { storiesOf } from "@storybook/react";
import * as React from "react";

import StaffDetailsPage from "../../../staff/components/StaffDetailsPage";
import { staff } from "../../../staff/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Staff / Member details ", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <StaffDetailsPage
      member={staff[0]}
      groups={staff[0].groups.edges.map(edge => edge.node)}
      searchGroupResults={staff[0].groups.edges.map(edge => edge.node)}
      onBack={() => {}}
      onStaffDelete={() => {}}
    />
  ))
  .add("other", () => <StaffDetailsPage disabled />);
