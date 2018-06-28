import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import * as CRC from "crc-32";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import StaffGroups from "../StaffGroups/StaffGroups";
import StaffProperties from "../StaffProperties/StaffProperties";

interface StaffDetailsPageProps {
  member?: {
    id: string;
    email?: string;
    isActive?: boolean;
  };
  groups?: Array<{
    id: string;
    name?: string;
  }>;
  searchGroupResults?: Array<{
    id: string;
    name?: string;
  }>;
  disabled?: boolean;
  loadingSearchGroupResults?: boolean;
  saveButtonBarState?: "loading" | "success" | "error" | "default" | string;
  onBack?: () => void;
  onGroupAdd?: (data: { group: { label: string; value: string } }) => void;
  onGroupDelete?: (id: string) => () => void;
  onGroupSearch?: (name: string) => void;
  onStaffDelete?: () => void;
  onSubmit?();
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "2fr 1fr"
  }
}));
const StaffDetailsPage = decorate<StaffDetailsPageProps>(
  ({
    classes,
    member,
    groups,
    searchGroupResults,
    disabled,
    loadingSearchGroupResults,
    saveButtonBarState,
    onBack,
    onGroupAdd,
    onGroupDelete,
    onGroupSearch,
    onStaffDelete,
    onSubmit
  }) => (
    <Toggle>
      {(openedDeleteDialog, { toggle: toggleDeleteDialog }) => (
        <Toggle>
          {(openedSearchGroupDialog, { toggle: toggleSearchGroupDialog }) => (
            <Container width="md">
              <PageHeader
                title={member ? member.email : undefined}
                onBack={onBack}
              >
                <IconButton
                  disabled={disabled || !onStaffDelete}
                  onClick={toggleDeleteDialog}
                >
                  <DeleteIcon />
                </IconButton>
              </PageHeader>
              <Form
                initial={{
                  email: member && member.email ? member.email : "",
                  isActive:
                    member && member.isActive !== undefined
                      ? member.isActive
                      : false
                }}
                key={member ? CRC.str(JSON.stringify(member)) : "loading"}
                onSubmit={onSubmit}
              >
                {({ change, data, hasChanged, submit }) => (
                  <>
                    <div className={classes.root}>
                      <div>
                        <StaffProperties
                          data={data}
                          disabled={disabled}
                          onChange={change}
                        />
                      </div>
                      <div>
                        <StaffGroups
                          groups={groups}
                          onGroupAdd={toggleSearchGroupDialog}
                          onGroupDelete={onGroupDelete}
                        />
                      </div>
                    </div>
                    <SaveButtonBar
                      onSave={submit}
                      state={saveButtonBarState}
                      disabled={disabled || !hasChanged}
                    />
                  </>
                )}
              </Form>
              {member && (
                <>
                  <ActionDialog
                    open={openedDeleteDialog}
                    variant="delete"
                    title={i18n.t("Remove staff member")}
                    onClose={toggleDeleteDialog}
                    onConfirm={onStaffDelete}
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ email }}</strong> from staff?",
                          { email: member.email }
                        )
                      }}
                    />
                  </ActionDialog>
                  <Form
                    initial={{ group: { label: "", value: "" } }}
                    onSubmit={onGroupAdd}
                  >
                    {({ change, data, submit }) => (
                      <ActionDialog
                        open={openedSearchGroupDialog}
                        title={i18n.t("Add staff member to group")}
                        onClose={toggleSearchGroupDialog}
                        onConfirm={submit}
                      >
                        <SingleAutocompleteSelectField
                          choices={
                            searchGroupResults
                              ? searchGroupResults.map(s => ({
                                  label: s.name,
                                  value: s.id
                                }))
                              : []
                          }
                          name="group"
                          onChange={change}
                          label={i18n.t("Group")}
                          loading={loadingSearchGroupResults}
                          fetchChoices={onGroupSearch}
                          value={data.group}
                        />
                      </ActionDialog>
                    )}
                  </Form>
                </>
              )}
            </Container>
          )}
        </Toggle>
      )}
    </Toggle>
  )
);
StaffDetailsPage.displayName = "StaffDetailsPage";
export default StaffDetailsPage;
