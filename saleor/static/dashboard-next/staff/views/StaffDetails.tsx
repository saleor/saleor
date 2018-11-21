import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../components/ActionDialog";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import StaffDetailsPage from "../components/StaffDetailsPage/StaffDetailsPage";
import {
  TypedStaffMemberDeleteMutation,
  TypedStaffMemberUpdateMutation
} from "../mutations";
import { TypedStaffMemberDetailsQuery } from "../queries";
import { StaffMemberDelete } from "../types/StaffMemberDelete";
import { StaffMemberUpdate } from "../types/StaffMemberUpdate";
import {
  staffListUrl,
  staffMemberDetailsUrl,
  staffMemberRemoveUrl
} from "../urls";

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
              const handleStaffMemberDelete = (data: StaffMemberDelete) => {
                if (!maybe(() => data.staffDelete.errors.length !== 0)) {
                  pushMessage({
                    text: i18n.t("Succesfully removed staff member")
                  });
                  navigate(staffListUrl);
                }
              };
              return (
                <TypedStaffMemberUpdateMutation
                  onCompleted={handleStaffMemberUpdate}
                >
                  {updateStaffMember => (
                    <TypedStaffMemberDeleteMutation
                      variables={{ id }}
                      onCompleted={handleStaffMemberDelete}
                    >
                      {deleteStaffMember => (
                        <>
                          <WindowTitle title={maybe(() => data.user.email)} />
                          <StaffDetailsPage
                            disabled={loading}
                            onBack={() => navigate(staffListUrl)}
                            onDelete={() => navigate(staffMemberRemoveUrl(id))}
                            onSubmit={variables =>
                              updateStaffMember({
                                variables: {
                                  id,
                                  input: {
                                    isActive: variables.isActive,
                                    permissions: variables.permissions
                                  }
                                }
                              })
                            }
                            permissions={maybe(() => data.shop.permissions)}
                            staffMember={maybe(() => data.user)}
                          />
                          <Route
                            path={staffMemberRemoveUrl(id)}
                            render={({ match }) => (
                              <ActionDialog
                                open={!!match}
                                title={i18n.t("Remove staff user")}
                                variant="delete"
                                onClose={() =>
                                  navigate(staffMemberDetailsUrl(id))
                                }
                                onConfirm={deleteStaffMember}
                              >
                                <DialogContentText
                                  dangerouslySetInnerHTML={{
                                    __html: i18n.t(
                                      "Are you sure you want to remove <strong>{{ email }}</strong> from staff members?",
                                      { email: maybe(() => data.user.email) }
                                    )
                                  }}
                                />
                              </ActionDialog>
                            )}
                          />
                        </>
                      )}
                    </TypedStaffMemberDeleteMutation>
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
