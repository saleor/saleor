import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import i18n from "../../../i18n";
import { getUserName, maybe } from "../../../misc";
import { PermissionEnum } from "../../../types/globalTypes";
import {
  StaffMemberDetails_shop_permissions,
  StaffMemberDetails_user
} from "../../types/StaffMemberDetails";
import StaffPermissions from "../StaffPermissions/StaffPermissions";
import StaffProperties from "../StaffProperties/StaffProperties";
import StaffStatus from "../StaffStatus/StaffStatus";

interface FormData {
  hasFullAccess: boolean;
  isActive: boolean;
  permissions: PermissionEnum[];
  firstName: string;
  lastName: string;
  email: string;
}

export interface StaffDetailsPageProps {
  canEditAvatar: boolean;
  canEditStatus: boolean;
  canRemove: boolean;
  disabled: boolean;
  permissions: StaffMemberDetails_shop_permissions[];
  saveButtonBarState: ConfirmButtonTransitionState;
  staffMember: StaffMemberDetails_user;
  onBack: () => void;
  onDelete: () => void;
  onImageDelete: () => void;
  onSubmit: (data: FormData) => void;
  onImageUpload(file: File);
}

const StaffDetailsPage: React.StatelessComponent<StaffDetailsPageProps> = ({
  canEditAvatar,
  canEditStatus,
  canRemove,
  disabled,
  permissions,
  saveButtonBarState,
  staffMember,
  onBack,
  onDelete,
  onImageDelete,
  onImageUpload,
  onSubmit
}: StaffDetailsPageProps) => {
  const initialForm: FormData = {
    email: maybe(() => staffMember.email),
    firstName: maybe(() => staffMember.firstName),
    hasFullAccess: maybe(
      () =>
        permissions.filter(
          perm =>
            maybe(() => staffMember.permissions, []).filter(
              userPerm => userPerm.code === perm.code
            ).length === 0
        ).length === 0,
      false
    ),
    isActive: maybe(() => staffMember.isActive, false),
    lastName: maybe(() => staffMember.lastName),
    permissions: maybe(() => staffMember.permissions, []).map(perm => perm.code)
  };
  return (
    <Form initial={initialForm} onSubmit={onSubmit} confirmLeave>
      {({ data, change, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Staff Members")}</AppHeader>
          <PageHeader title={getUserName(staffMember)} />
          <Grid>
            <div>
              <StaffProperties
                data={data}
                disabled={disabled}
                canEditAvatar={canEditAvatar}
                staffMember={staffMember}
                onChange={change}
                onImageUpload={onImageUpload}
                onImageDelete={onImageDelete}
              />
            </div>
            {canEditStatus && (
              <div>
                <StaffPermissions
                  data={data}
                  disabled={disabled}
                  permissions={permissions}
                  onChange={change}
                />
                <CardSpacer />
                <StaffStatus
                  data={data}
                  disabled={disabled}
                  onChange={change}
                />
              </div>
            )}
          </Grid>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            state={saveButtonBarState}
            onCancel={onBack}
            onSave={submit}
            onDelete={canRemove ? onDelete : undefined}
          />
        </Container>
      )}
    </Form>
  );
};
StaffDetailsPage.displayName = "StaffDetailsPage";
export default StaffDetailsPage;
