import IconButton from "@material-ui/core/IconButton";
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
      sortNumber: number;
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
      <IconButton disabled={disabled} onClick={onAdd}>
        <AddIcon />
      </IconButton>
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
