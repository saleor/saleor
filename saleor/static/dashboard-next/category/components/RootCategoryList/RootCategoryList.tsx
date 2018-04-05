import AddIcon from "material-ui-icons/Add";
import Card from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import CategoryList from "../../../components/CategoryList";
import PageHeader from "../../../components/PageHeader";
import { RootCategoryChildrenQuery } from "../../../gql-types";
import i18n from "../../../i18n";

interface RootCategoryListProps {
  categories?: Array<{
    id: string;
    name: string;
  }>;
  onClick?(id: string);
  onCreate?();
}

const RootCategoryList: React.StatelessComponent<RootCategoryListProps> = ({
  categories,
  onClick,
  onCreate
}) => (
  <Card>
    <PageHeader title={i18n.t("Categories", { context: "title" })}>
      <IconButton onClick={onCreate}>
        <AddIcon />
      </IconButton>
    </PageHeader>
    <CategoryList categories={categories} onClick={onClick} />
  </Card>
);

export default RootCategoryList;
