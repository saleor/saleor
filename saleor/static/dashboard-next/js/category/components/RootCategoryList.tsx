import AddIcon from "material-ui-icons/Add";
import Card from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";
import CategoryList from "./CategoryList";

const RootCategoryList = ({ data, loading, onCreate }) => (
  <Card>
    <PageHeader title={i18n.t("Categories", { context: "title" })}>
      <IconButton onClick={onCreate} disabled={loading}>
        <AddIcon />
      </IconButton>
    </PageHeader>
    <CategoryList categories={data.categories && data.categories.edges} />
  </Card>
);

export default RootCategoryList;
