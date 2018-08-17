import Button from "@material-ui/core/Button";
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
  cardContainer: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: {
      marginTop: theme.spacing.unit
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
                onBack={isRoot ? undefined : onBack}
                title={
                  isRoot
                    ? i18n.t("Categories")
                    : category
                      ? category.name
                      : undefined
                }
              >
                {isRoot && (
                  <Button
                    color="secondary"
                    variant="contained"
                    onClick={onAddCategory}
                  >
                    {i18n.t("Add category")} <AddIcon />
                  </Button>
                )}
              </PageHeader>
              <div>
                {!isRoot && (
                  <CategoryProperties
                    description={category ? category.description : undefined}
                    onEdit={onEdit}
                    onDelete={toggleDialog}
                  />
                )}
                <div className={isRoot ? undefined : classes.cardContainer}>
                  <CategoryList
                    categories={subcategories}
                    displayTitle={!isRoot}
                    onAdd={onAddCategory}
                    onRowClick={onCategoryClick}
                  />
                </div>
                {!isRoot && (
                  <div className={classes.cardContainer}>
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
                  </div>
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
