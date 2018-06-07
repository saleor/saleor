import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import CategoryDeleteDialog from "../../components/CategoryDeleteDialog";
import CategoryList from "../../components/CategoryList";
import CategoryProperties from "../../components/CategoryProperties";
import CategoryProducts from "../CategoryProducts";

interface CategoryDetailsPageProps {
  category?: {
    id: string;
    description?: string;
    name?: string;
  };
  subcategories?: Array<{
    id: string;
    name: string;
  }>;
  products?: Array<{
    id: string;
    name: string;
    thumbnailUrl: string;
    productType: {
      name: string;
    };
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  productCount?: number;
  loading?: boolean;
  onAddCategory?();
  onAddProduct?();
  onBack?();
  onCategoryClick?(id: string): () => void;
  onDelete?();
  onEdit?();
  onNextPage?();
  onPreviousPage?();
  onProductClick?(id: string): () => void;
}

const decorate = withStyles(theme => ({
  root: {
    "& > *": {
      marginBottom: theme.spacing.unit * 2,
      [theme.breakpoints.down("md")]: {
        marginBottom: theme.spacing.unit
      }
    }
  }
}));
const CategoryDetailsPage = decorate<CategoryDetailsPageProps>(
  ({
    category,
    classes,
    loading,
    pageInfo,
    productCount,
    products,
    subcategories,
    onAddCategory,
    onAddProduct,
    onBack,
    onCategoryClick,
    onDelete,
    onEdit,
    onNextPage,
    onPreviousPage,
    onProductClick
  }) => {
    const isRoot = !loading && !products && !category;
    return (
      <Toggle>
        {(opened, { toggle: toggleDialog }) => (
          <>
            <Container width="md">
              <PageHeader
                onBack={!isRoot ? onBack : undefined}
                title={
                  !isRoot
                    ? category
                      ? category.name
                      : undefined
                    : i18n.t("Categories")
                }
              >
                {!!onAddProduct &&
                  isRoot && (
                    <IconButton onClick={onAddProduct}>
                      <AddIcon />
                    </IconButton>
                  )}
              </PageHeader>
              <div className={classes.root}>
                {!isRoot && (
                  <CategoryProperties
                    description={category ? category.description : undefined}
                    onEdit={onEdit}
                    onDelete={toggleDialog}
                  />
                )}
                <CategoryList
                  categories={subcategories}
                  displayTitle={!isRoot}
                  onAdd={onAddCategory}
                  onRowClick={onCategoryClick}
                />
                {!isRoot && (
                  <CategoryProducts
                    products={products}
                    hasNextPage={pageInfo ? pageInfo.hasNextPage : false}
                    hasPreviousPage={
                      pageInfo ? pageInfo.hasPreviousPage : false
                    }
                    onAddProduct={onAddProduct}
                    onNextPage={onNextPage}
                    onPreviousPage={onPreviousPage}
                    onRowClick={onProductClick}
                  />
                )}
              </div>
            </Container>
            {category && (
              <CategoryDeleteDialog
                name={category.name}
                open={opened}
                productCount={productCount}
                onClose={toggleDialog}
                onConfirm={onDelete}
              />
            )}
          </>
        )}
      </Toggle>
    );
  }
);
export default CategoryDetailsPage;
