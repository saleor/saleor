import * as React from "react";

import { staffListUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import StaffDetailsPage from "../components/StaffDetailsPage/StaffDetailsPage";
import { TypedStaffMemberUpdateMutation } from "../mutations";
import { TypedStaffMemberDetailsQuery } from "../queries";
import { StaffMemberUpdate } from "../types/StaffMemberUpdate";

interface OrderListProps {
  id: string;
}

export const StaffDetails: React.StatelessComponent<OrderListProps> = ({
  id
}) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => (
          <TypedStaffMemberDetailsQuery variables={{ id }}>
            {({ data, loading }) => {
              const handleStaffMemberUpdate = (data: StaffMemberUpdate) => {
                if (!maybe(() => data.staffUpdate.errors.length !== 0)) {
                  pushMessage({
                    text: i18n.t("Succesfully updated staff member account")
                  });
                }
              };
              return (
                <TypedStaffMemberUpdateMutation
                  onCompleted={handleStaffMemberUpdate}
                >
                  {updateStaffMember => (
                    <StaffDetailsPage
                      disabled={loading}
                      onBack={() => navigate(staffListUrl)}
                      onDelete={() => undefined}
                      onSubmit={variables =>
                        updateStaffMember({
                          variables: {
                            id,
                            input: {
                              permissions: variables.permissions
                            }
                          }
                        })
                      }
                      permissions={maybe(() => data.shop.permissions)}
                      staffMember={maybe(() => data.user)}
                    />
                  )}
                </TypedStaffMemberUpdateMutation>
              );
            }}
          </TypedStaffMemberDetailsQuery>
        )}
      </Messages>
    )}
  </Navigator>
);

export default StaffDetails;
