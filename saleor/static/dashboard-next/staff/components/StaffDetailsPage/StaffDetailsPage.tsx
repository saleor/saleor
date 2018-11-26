import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import { maybe } from "../../../misc";
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
  permissions: string[];
}

export interface StaffDetailsPageProps {
  disabled: boolean;
  permissions: StaffMemberDetails_shop_permissions[];
  saveButtonBarState: ConfirmButtonTransitionState;
  staffMember: StaffMemberDetails_user;
  onBack: () => void;
  onDelete: () => void;
  onSubmit: (data: FormData) => void;
}

const decorate = withStyles(theme => ({
  card: {
    marginBottom: theme.spacing.unit * 2 + "px"
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "9fr 4fr"
  }
}));
const StaffDetailsPage = decorate<StaffDetailsPageProps>(
  ({
    classes,
    disabled,
    permissions,
    saveButtonBarState,
    staffMember,
    onBack,
    onDelete,
    onSubmit
  }) => {
    const initialForm: FormData = {
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
      permissions: maybe(() => staffMember.permissions, []).map(
        perm => perm.code
      )
    };
    return (
      <Form
        initial={initialForm}
        onSubmit={onSubmit}
        key={JSON.stringify({ staffMember, permissions })}
      >
        {({ data, change, hasChanged, submit }) => (
          <Container width="md">
            <PageHeader
              title={maybe(() => staffMember.email)}
              onBack={onBack}
            />
            <div className={classes.root}>
              <div>
                <StaffProperties
                  className={classes.card}
                  staffMember={staffMember}
                />
              </div>
              <div>
                <div className={classes.card}>
                  <StaffPermissions
                    data={data}
                    disabled={disabled}
                    permissions={permissions}
                    onChange={change}
                  />
                </div>
                <StaffStatus
                  data={data}
                  disabled={disabled}
                  onChange={change}
                />
              </div>
            </div>
            <SaveButtonBar
              disabled={disabled || !hasChanged}
              state={saveButtonBarState}
              onCancel={onBack}
              onSave={submit}
              onDelete={onDelete}
            />
          </Container>
        )}
      </Form>
    );
  }
);
StaffDetailsPage.displayName = "StaffDetailsPage";
export default StaffDetailsPage;
