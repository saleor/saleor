import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import { AttributeList_attributes_edges_node } from "../../types/AttributeList";
import AttributeList from "../AttributeList/AttributeList";

export interface AttributeListPageProps extends PageListProps, ListActions {
  attributes: AttributeList_attributes_edges_node[];
}

const AttributeListPage: React.FC<AttributeListPageProps> = ({
  onAdd,
  ...listProps
}) => (
  <Container>
    <PageHeader title={i18n.t("Attributes")}>
      <Button onClick={onAdd} color="primary" variant="contained">
        {i18n.t("Add attribute")} <AddIcon />
      </Button>
    </PageHeader>
    <Card>
      <AttributeList {...listProps} />
    </Card>
  </Container>
);
AttributeListPage.displayName = "AttributeListPage";
export default AttributeListPage;
