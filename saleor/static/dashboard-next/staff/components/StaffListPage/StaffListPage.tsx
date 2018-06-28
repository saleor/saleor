import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import StaffList from "../StaffList";

interface StaffListPageProps {
  staff?: Array<{
    id: string;
    email?: string;
    groups?: {
      totalCount: number;
    };
    isActive?: boolean;
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  onAddStaff?: () => void;
  onNextPage?: () => void;
  onPreviousPage?: () => void;
  onRowClick?: (id: string) => () => void;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main
  }
}));
const StaffListPage = decorate<StaffListPageProps>(
  ({
    classes,
    staff,
    pageInfo,
    onAddStaff,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Container width="md">
      <PageHeader title={i18n.t("Staff members")}>
        <IconButton onClick={onAddStaff} disabled={!onAddStaff}>
          <AddIcon />
        </IconButton>
      </PageHeader>
      <StaffList
        staff={staff}
        pageInfo={pageInfo}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
        onRowClick={onRowClick}
      />
    </Container>
  )
);
StaffListPage.displayName = "StaffListPage";
export default StaffListPage;
