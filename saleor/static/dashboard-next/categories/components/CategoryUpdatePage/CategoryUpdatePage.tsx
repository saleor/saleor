import { withStyles } from "@material-ui/core/styles";
import * as React from "react";
import AddIcon from "@material-ui/icons/Add";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";

import CategoryBackground from "../CategoryBackground";
import CategoryList from "../../components/CategoryList";

import CategoryDetailsForm from "../../components/CategoryDetailsForm";
import SeoForm from "../../../components/SeoForm";
import Form from "../../../components/Form";
import CategoryProductsCard from "../CategoryProductsCard";
import CategoryDeleteDialog from "../../components/CategoryDeleteDialog";
import { MoneyType } from "../../../products";
import Toggle from "../../../components/Toggle";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar/SaveButtonBar";

import Tabs, { SingleTab } from "../../../components/Tab";

import { UserError } from "../../../";
// import Card from "@material-ui/core/Card";
import Button from "@material-ui/core/Button";
// import CardContent from "@material-ui/core/CardContent";
// import AddPhotoIcon from "@material-ui/icons/AddAPhoto";
// import Typography from "@material-ui/core/Typography";
// import CardTitle from "../../../components/CardTitle";

import i18n from "../../../i18n";

interface FormData {
  //CategoryDetailsForm
  description: string;
  name: string;

  // SeoForm
  seoTitle: string;
  seoDescription: string;
}
interface CategoryUpdatePageProps {
  errors: UserError[];
  disabled: boolean;
  productCount?: number;
  category?: {
    SeoDescription?: string;
    SeoTitle?: string;
    name?: string;
    description?: string;
  };
  products?: Array<{
    id: string;
    name: string;
    productType: {
      name: string;
    };
    thumbnailUrl: string;
    availability: {
      available: boolean;
    };
    price: MoneyType;
  }>;
  subcategories?: Array<{
    id: string;
    name: string;
    children: {
      totalCount: number;
    };
    products: {
      totalCount: number;
    };
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  loading: boolean;
  saveButtonBarState?: SaveButtonBarState;
  onSubmit?(data: FormData);
  onImageUpload?(event: React.ChangeEvent<any>);
  onNextPage?();
  onPreviousPage?();
  onProductClick?(id: string): () => void;
  onAddProduct?();
  onBack?();
  onDelete?();
  onSubmit?(data: FormData);
  onAddCategory?();
  onCategoryClick?(id: string): () => void;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    marginTop: theme.spacing.unit * 2,
    gridGap: theme.spacing.unit * 4 + "px"
  },
  tabsBorder: {
    borderBottom: "1px solid #eeeeee"
  }
}));

export const CategoryUpdatePage = decorate<CategoryUpdatePageProps>(
  ({
    classes,
    disabled,
    errors: userErrors,
    category,
    onImageUpload,
    subcategories,
    loading,
    products,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onProductClick,
    onAddProduct,
    onDelete,
    saveButtonBarState,
    onSubmit,
    onBack,
    productCount,
    onAddCategory,
    onCategoryClick
  }) => {
    const initialData = category
      ? {
          name: category.name,
          description: category.description,
          seoTitle: category.SeoTitle,
          seoDescription: category.SeoTitle
        }
      : {
          name: "",
          description: "",
          seoTitle: "",
          seoDescription: ""
        };
    const isRoot = !loading && !products && !category;
    return (
      <Toggle>
        {(openedDeleteDialog, { toggle: toggleDeleteDialog }) => (
          <Form onSubmit={onSubmit} initial={initialData} errors={userErrors}>
            {({ data, change, errors, submit, hasChanged }) => (
              <>
                <Container width="lg">
                  <PageHeader
                    title={
                      isRoot
                        ? i18n.t("Category")
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

                  <div className={classes.root}>
                    {!isRoot && (
                      <>
                        <CategoryDetailsForm
                          data={data}
                          disabled={disabled}
                          errors={errors}
                          onChange={change}
                          loading={loading}
                        />
                        <CategoryBackground
                          onImageUpload={onImageUpload}
                          disabled={disabled}
                        />
                        <SeoForm
                          helperText={i18n.t(
                            "Add search engine title and description to make this product easier to find"
                          )}
                          title={data.seoTitle}
                          titlePlaceholder={data.name}
                          description={data.seoDescription}
                          descriptionPlaceholder={data.description}
                          loading={loading}
                          onChange={change}
                          disabled={disabled}
                        />
                      </>
                    )}
                    {isRoot && (
                      <CategoryList
                        categories={subcategories}
                        isRoot={isRoot}
                        onAdd={onAddCategory}
                        onRowClick={onCategoryClick}
                      />
                    )}
                    {!isRoot && (
                      <>
                        <Tabs>
                          {({ changeTab, currentTab }) => (
                            <>
                              <div className={classes.tabsBorder}>
                                <SingleTab
                                  isActive={currentTab === 0}
                                  value={0}
                                  changeTab={changeTab}
                                >
                                  Subcategories
                                </SingleTab>
                                <SingleTab
                                  isActive={currentTab === 1}
                                  value={1}
                                  changeTab={changeTab}
                                >
                                  Products
                                </SingleTab>
                              </div>
                              {currentTab === 0 && (
                                <CategoryList
                                  categories={subcategories}
                                  isRoot={isRoot}
                                  onAdd={onAddCategory}
                                  onRowClick={onCategoryClick}
                                />
                              )}
                              {currentTab === 1 && (
                                <CategoryProductsCard
                                  products={products}
                                  disabled={disabled}
                                  pageInfo={pageInfo}
                                  onNextPage={onNextPage}
                                  onPreviousPage={onPreviousPage}
                                  onRowClick={onProductClick}
                                  onAdd={onAddProduct}
                                />
                              )}
                            </>
                          )}
                        </Tabs>
                        <SaveButtonBar
                          onCancel={onBack}
                          onDelete={toggleDeleteDialog}
                          onSave={submit}
                          labels={{
                            save: i18n.t("Save category"),
                            delete: i18n.t("Delete category")
                          }}
                          state={saveButtonBarState}
                          disabled={disabled || !hasChanged}
                        />
                      </>
                    )}
                  </div>
                </Container>
                {!isRoot && (
                  <CategoryDeleteDialog
                    name={category.name}
                    open={openedDeleteDialog}
                    productCount={productCount}
                    onClose={toggleDeleteDialog}
                    onConfirm={onDelete}
                  />
                )}
              </>
            )}
          </Form>
        )}
      </Toggle>
    );
  }
);
export default CategoryUpdatePage;
