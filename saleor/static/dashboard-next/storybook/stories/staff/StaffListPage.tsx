import { storiesOf } from "@storybook/react";
import * as React from "react";

import { listActionsProps, pageListProps } from "../../../fixtures";
import StaffListPage, {
  StaffListPageProps
} from "../../../staff/components/StaffListPage";
import { staffMembers } from "../../../staff/fixtures";
import Decorator from "../../Decorator";

const props: StaffListPageProps = {
  onAdd: undefined,
  onBack: () => undefined,
  staffMembers,
  ...listActionsProps,
  ...pageListProps.default
};

storiesOf("Views / Staff / Staff members", module)
  .addDecorator(Decorator)
  .add("default", () => <StaffListPage {...props} />)
  .add("when loading", () => (
    <StaffListPage {...props} disabled={true} staffMembers={undefined} />
  ));
