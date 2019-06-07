import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "@components/ActionDialog";
import { WindowTitle } from "@components/WindowTitle";
import useNavigator from "@hooks/useNavigator";
import useNotifier from "@hooks/useNotifier";
import useUser from "@hooks/useUser";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import StaffDetailsPage from "../components/StaffDetailsPage/StaffDetailsPage";
import {
  TypedStaffAvatarDeleteMutation,
  TypedStaffAvatarUpdateMutation,
  TypedStaffMemberDeleteMutation,
  TypedStaffMemberUpdateMutation
} from "../mutations";
import { TypedStaffMemberDetailsQuery } from "../queries";
import { StaffAvatarDelete } from "../types/StaffAvatarDelete";
import { StaffAvatarUpdate } from "../types/StaffAvatarUpdate";
import { StaffMemberDelete } from "../types/StaffMemberDelete";
import { StaffMemberUpdate } from "../types/StaffMemberUpdate";
import {
  staffListUrl,
  staffMemberDetailsUrl,
  StaffMemberDetailsUrlQueryParams
} from "../urls";

interface OrderListProps {
  id: string;
  params: StaffMemberDetailsUrlQueryParams;
}

export const StaffDetails: React.StatelessComponent<OrderListProps> = ({
  id,
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const user = useUser();

  return (
    <TypedStaffMemberDetailsQuery
      displayLoader
      variables={{ id }}
      require={["user"]}
    >
      {({ data, loading }) => {
        const handleStaffMemberUpdate = (data: StaffMemberUpdate) => {
          if (!maybe(() => data.staffUpdate.errors.length !== 0)) {
            notify({
              text: i18n.t("Succesfully updated staff member account")
            });
          }
        };
        const handleStaffMemberDelete = (data: StaffMemberDelete) => {
          if (!maybe(() => data.staffDelete.errors.length !== 0)) {
            notify({
              text: i18n.t("Succesfully removed staff member")
            });
            navigate(staffListUrl());
          }
        };
        const handleStaffMemberAvatarUpdate = (data: StaffAvatarUpdate) => {
          if (!maybe(() => data.userAvatarUpdate.errors.length !== 0)) {
            notify({
              text: i18n.t("Succesfully updated staff member avatar")
            });
          }
        };
        const handleStaffMemberAvatarDelete = (data: StaffAvatarDelete) => {
          if (!maybe(() => data.userAvatarDelete.errors.length !== 0)) {
            notify({
              text: i18n.t("Succesfully removed staff member avatar")
            });
            navigate(staffMemberDetailsUrl(id));
          }
        };
        return (
          <TypedStaffMemberUpdateMutation onCompleted={handleStaffMemberUpdate}>
            {(updateStaffMember, updateResult) => (
              <TypedStaffMemberDeleteMutation
                variables={{ id }}
                onCompleted={handleStaffMemberDelete}
              >
                {(deleteStaffMember, deleteResult) => (
                  <TypedStaffAvatarUpdateMutation
                    onCompleted={handleStaffMemberAvatarUpdate}
                  >
                    {updateStaffAvatar => (
                      <TypedStaffAvatarDeleteMutation
                        onCompleted={handleStaffMemberAvatarDelete}
                      >
                        {(deleteStaffAvatar, deleteAvatarResult) => {
                          const formTransitionState = getMutationState(
                            updateResult.called,
                            updateResult.loading,
                            maybe(() => updateResult.data.staffUpdate.errors)
                          );
                          const deleteTransitionState = getMutationState(
                            deleteResult.called,
                            deleteResult.loading,
                            maybe(() => deleteResult.data.staffDelete.errors)
                          );
                          const deleteAvatarTransitionState = getMutationState(
                            deleteAvatarResult.called,
                            deleteAvatarResult.loading,
                            maybe(
                              () =>
                                deleteAvatarResult.data.userAvatarDelete.errors
                            )
                          );
                          const isUserSameAsViewer = maybe(
                            () => user.user.id === data.user.id,
                            true
                          );

                          return (
                            <>
                              <WindowTitle
                                title={maybe(() => data.user.email)}
                              />
                              <StaffDetailsPage
                                canEditAvatar={isUserSameAsViewer}
                                canEditStatus={!isUserSameAsViewer}
                                canRemove={!isUserSameAsViewer}
                                disabled={loading}
                                onBack={() => navigate(staffListUrl())}
                                onDelete={() =>
                                  navigate(
                                    staffMemberDetailsUrl(id, {
                                      action: "remove"
                                    })
                                  )
                                }
                                onSubmit={variables =>
                                  updateStaffMember({
                                    variables: {
                                      id,
                                      input: {
                                        email: variables.email,
                                        firstName: variables.firstName,
                                        isActive: variables.isActive,
                                        lastName: variables.lastName,
                                        permissions: variables.permissions
                                      }
                                    }
                                  })
                                }
                                onImageUpload={file =>
                                  updateStaffAvatar({
                                    variables: {
                                      image: file
                                    }
                                  })
                                }
                                onImageDelete={() =>
                                  navigate(
                                    staffMemberDetailsUrl(id, {
                                      action: "remove-avatar"
                                    })
                                  )
                                }
                                permissions={maybe(() => data.shop.permissions)}
                                staffMember={maybe(() => data.user)}
                                saveButtonBarState={formTransitionState}
                              />
                              <ActionDialog
                                open={params.action === "remove"}
                                title={i18n.t("Remove staff user")}
                                confirmButtonState={deleteTransitionState}
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
                                      {
                                        email: maybe(() => data.user.email)
                                      }
                                    )
                                  }}
                                />
                              </ActionDialog>
                              <ActionDialog
                                open={params.action === "remove-avatar"}
                                title={i18n.t("Remove staff user avatar")}
                                confirmButtonState={deleteAvatarTransitionState}
                                variant="delete"
                                onClose={() =>
                                  navigate(staffMemberDetailsUrl(id))
                                }
                                onConfirm={deleteStaffAvatar}
                              >
                                <DialogContentText
                                  dangerouslySetInnerHTML={{
                                    __html: i18n.t(
                                      "Are you sure you want to remove <strong>{{ email }}</strong> avatar?",
                                      {
                                        email: maybe(() => data.user.email)
                                      }
                                    )
                                  }}
                                />
                              </ActionDialog>
                            </>
                          );
                        }}
                      </TypedStaffAvatarDeleteMutation>
                    )}
                  </TypedStaffAvatarUpdateMutation>
                )}
              </TypedStaffMemberDeleteMutation>
            )}
          </TypedStaffMemberUpdateMutation>
        );
      }}
    </TypedStaffMemberDetailsQuery>
  );
};

export default StaffDetails;
