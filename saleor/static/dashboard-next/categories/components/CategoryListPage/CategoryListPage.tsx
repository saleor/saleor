import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import CategoryList from "../CategoryList";

export interface CategoryTableProps {
  categories: Array<{
    id: string;
    name: string;
    children: {
      totalCount: number;
    };
    products: {
      totalCount: number;
    };
  }>;
  onAddCategory();
  onCategoryClick(id: string): () => void;
}

export const CategoryListPage: React.StatelessComponent<CategoryTableProps> = ({
  categories,
  onAddCategory,
  onCategoryClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Category")}>
      <Button color="secondary" variant="contained" onClick={onAddCategory}>
        {i18n.t("Add category")} <AddIcon />
      </Button>
    </PageHeader>
    <CategoryList
      categories={categories}
      onAdd={onAddCategory}
      onRowClick={onCategoryClick}
      isRoot={true}
    />
  </Container>
);
CategoryListPage.displayName = "CategoryListPage";
export default CategoryListPage;
