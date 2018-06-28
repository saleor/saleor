import { storiesOf } from "@storybook/react";
import * as React from "react";

import StaffListPage from "../../../staff/components/StaffListPage";
import { staff } from "../../../staff/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Staff / Staff list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <StaffListPage
      staff={staff}
      pageInfo={{ hasNextPage: true, hasPreviousPage: false }}
      onAddStaff={() => {}}
      onNextPage={() => {}}
      onPreviousPage={() => {}}
      onRowClick={() => () => {}}
    />
  ))
  .add("other", () => <StaffListPage />);
