import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListProps } from "../../../types";
import { StaffList_staffUsers_edges_node } from "../../types/StaffList";
import StaffList from "../StaffList/StaffList";

export interface StaffListPageProps extends ListProps {
  staffMembers: StaffList_staffUsers_edges_node[];
  onAdd: () => void;
  onBack: () => void;
}

const StaffListPage: React.StatelessComponent<StaffListPageProps> = ({
  disabled,
  onAdd,
  onBack,
  ...listProps
}) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Configuration")}</AppHeader>
    <PageHeader title={i18n.t("Staff members", { context: "page title" })}>
      <Button
        color="primary"
        disabled={disabled}
        variant="contained"
        onClick={onAdd}
      >
        {i18n.t("Add staff member", { context: "button" })}
        <AddIcon />
      </Button>
    </PageHeader>
    <StaffList disabled={disabled} {...listProps} />
  </Container>
);
StaffListPage.displayName = "StaffListPage";
export default StaffListPage;
