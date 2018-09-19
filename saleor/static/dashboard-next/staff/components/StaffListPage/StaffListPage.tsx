import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { Omit, PageListProps } from "../../..";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import { StaffList_staffUsers_edges_node } from "../../types/StaffList";
import StaffAddMemberDialog from "../StaffAddMemberDialog/StaffAddMemberDialog";
import StaffList from "../StaffList/StaffList";

export interface StaffListPageProps extends PageListProps {
  staffMembers: Array<Omit<StaffList_staffUsers_edges_node, "__typename">>;
}

const StaffListPage: React.StatelessComponent<StaffListPageProps> = ({
  disabled,
  pageInfo,
  staffMembers,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Toggle>
    {(openedAddStaffMemberDialog, { toggle: toggleAddStaffMemberDialog }) => (
      <Container width="md">
        <PageHeader title={i18n.t("Staff members", { context: "page title" })}>
          <Button
            color="secondary"
            disabled={disabled}
            variant="contained"
            onClick={toggleAddStaffMemberDialog}
          >
            {i18n.t("Add staff member", { context: "button" })}
            <AddIcon />
          </Button>
        </PageHeader>
        <StaffList
          disabled={disabled}
          pageInfo={pageInfo}
          staffMembers={staffMembers}
          onNextPage={onNextPage}
          onPreviousPage={onPreviousPage}
          onRowClick={onRowClick}
        />
        <StaffAddMemberDialog
          open={openedAddStaffMemberDialog}
          onClose={toggleAddStaffMemberDialog}
          onConfirm={onAdd}
        />
      </Container>
    )}
  </Toggle>
);
StaffListPage.displayName = "StaffListPage";
export default StaffListPage;
