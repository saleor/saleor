import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListActionProps, PageListProps } from "../../../types";
import CategoryList from "../CategoryList";

export interface CategoryTableProps
  extends PageListProps,
    ListActionProps<"onBulkDelete"> {
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
}

export const CategoryListPage: React.StatelessComponent<CategoryTableProps> = ({
  categories,
  disabled,
  onAdd,
  onBulkDelete,
  onNextPage,
  onPreviousPage,
  onRowClick,
  pageInfo
}) => (
  <Container>
    <PageHeader title={i18n.t("Categories")}>
      <Button color="primary" variant="contained" onClick={onAdd}>
        {i18n.t("Add category")} <AddIcon />
      </Button>
    </PageHeader>
    <CategoryList
      categories={categories}
      onAdd={onAdd}
      onBulkDelete={onBulkDelete}
      onRowClick={onRowClick}
      disabled={disabled}
      isRoot={true}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      pageInfo={pageInfo}
    />
  </Container>
);
CategoryListPage.displayName = "CategoryListPage";
export default CategoryListPage;
