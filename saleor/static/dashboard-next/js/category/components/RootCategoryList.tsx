import AddIcon from "material-ui-icons/Add";
import Card from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";
import { RootCategoryChildrenQuery } from "../gql-types";
import CategoryList from "./CategoryList";

interface RootCategoryListProps {
  data: RootCategoryChildrenQuery;
  loading?: boolean;
  onClick?(id: string);
  onCreate?();
}

const RootCategoryList: React.StatelessComponent<RootCategoryListProps> = ({
  data,
  loading,
  onClick,
  onCreate
}) => (
  <Card>
    <PageHeader title={i18n.t("Categories", { context: "title" })}>
      <IconButton onClick={onCreate} disabled={loading}>
        <AddIcon />
      </IconButton>
    </PageHeader>
    <CategoryList
      categories={data.categories && data.categories.edges}
      onClick={onClick}
    />
  </Card>
);

export default RootCategoryList;
