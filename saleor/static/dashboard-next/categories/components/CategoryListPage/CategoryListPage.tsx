import Button from "@material-ui/core/Button";
import { withStyles } from "@material-ui/core/styles";
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

const decorate = withStyles({});

export const CategoryListPage = decorate<CategoryTableProps>(
  ({ categories, onAddCategory, onCategoryClick }) => {
    return (
      <>
        <Container width="md">
          <PageHeader title={i18n.t("Category")}>
            <Button
              color="secondary"
              variant="contained"
              onClick={onAddCategory}
            >
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
      </>
    );
  }
);
export default CategoryListPage;
