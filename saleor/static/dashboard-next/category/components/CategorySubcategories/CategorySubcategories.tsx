import AddIcon from "@material-ui/icons/Add";
import Card from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import * as React from "react";

import CategoryList from "../../../components/CategoryList";
import PageHeader from "../../../components/PageHeader";
import { CategoryPropertiesQuery } from "../../../gql-types";
import i18n from "../../../i18n";

interface CategorySubcategoriesProps {
  subcategories?: Array<{
    id: string;
    name: string;
  }>;
  onClickSubcategory?(id: string);
  onCreate?();
}

const CategorySubcategories: React.StatelessComponent<
  CategorySubcategoriesProps
> = ({ subcategories, onClickSubcategory, onCreate }) => (
  <Card>
    <PageHeader
      title={i18n.t("Subcategories", {
        context: "title"
      })}
    >
      <IconButton onClick={onCreate}>
        <AddIcon />
      </IconButton>
    </PageHeader>
    <CategoryList categories={subcategories} onClick={onClickSubcategory} />
  </Card>
);

export default CategorySubcategories;
