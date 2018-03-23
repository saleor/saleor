import AddIcon from "material-ui-icons/Add";
import Card from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import CategoryList from "../../components/CategoryList";
import PageHeader from "../../components/PageHeader";
import { CategoryPropertiesQuery } from "../../gql-types";
import i18n from "../../i18n";

interface CategorySubcategoriesProps {
  data: CategoryPropertiesQuery;
  loading?: boolean;
  onClickSubcategory?(id: string);
  onCreate?();
}

const CategorySubcategories: React.StatelessComponent<
  CategorySubcategoriesProps
> = ({ data, loading, onClickSubcategory, onCreate }) => (
  <Card>
    <PageHeader
      title={i18n.t("Subcategories", {
        context: "title"
      })}
    >
      <IconButton disabled={loading} onClick={onCreate}>
        <AddIcon />
      </IconButton>
    </PageHeader>
    <CategoryList
      categories={
        data.category && data.category.children && data.category.children.edges
      }
      onClick={onClickSubcategory}
    />
  </Card>
);

export default CategorySubcategories;
