import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../../";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import AttributeList from "../AttributeList/AttributeList";

interface AttributeListPageProps extends PageListProps {
  attributes?: Array<{
    id: string;
    name: string;
    values: Array<{
      id: string;
      sortOrder: number;
      name: string;
    }>;
  }>;
}

const AttributeListPage: React.StatelessComponent<AttributeListPageProps> = ({
  attributes,
  disabled,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Attributes")}>
      <Button
        color="secondary"
        variant="contained"
        disabled={disabled}
        onClick={onAdd}
      >
        {i18n.t("Add attribute")} <AddIcon />
      </Button>
    </PageHeader>
    <AttributeList
      attributes={attributes}
      disabled={disabled}
      pageInfo={pageInfo}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
    />
  </Container>
);
AttributeListPage.displayName = "AttributeListPage";
export default AttributeListPage;
