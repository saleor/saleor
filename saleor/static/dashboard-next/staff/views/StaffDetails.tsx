import * as React from "react";

import { staffListUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { maybe } from "../../misc";
import StaffDetailsPage from "../components/StaffDetailsPage/StaffDetailsPage";
import { TypedStaffMemberDetailsQuery } from "../queries";

interface OrderListProps {
  id: string;
}

export const StaffDetails: React.StatelessComponent<OrderListProps> = ({
  id
}) => (
  <Navigator>
    {navigate => (
      <Messages>
        {_ => (
          <TypedStaffMemberDetailsQuery variables={{ id }}>
            {({ data, loading }) => {
              return (
                <StaffDetailsPage
                  disabled={loading}
                  onBack={() => navigate(staffListUrl)}
                  onDelete={() => undefined}
                  onSubmit={() => undefined}
                  permissions={maybe(() => data.shop.permissions)}
                  staffMember={maybe(() => data.user)}
                />
              );
            }}
          </TypedStaffMemberDetailsQuery>
        )}
      </Messages>
    )}
  </Navigator>
);

export default StaffDetails;
