import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { CardSpacer } from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import Tabs, { Tab } from "../../../components/Tab";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import CategoryDetailsForm from "../../components/CategoryDetailsForm";
import CategoryList from "../../components/CategoryList";
import {
  CategoryDetails_category,
  CategoryDetails_category_children_edges_node,
  CategoryDetails_category_products_edges_node
} from "../../types/CategoryDetails";
// import CategoryBackground from "../CategoryBackground";
import CategoryProductsCard from "../CategoryProductsCard";

interface FormData {
  description: string;
  name: string;
  seoTitle: string;
  seoDescription: string;
}

export interface CategoryUpdatePageProps {
  errors: UserError[];
  disabled: boolean;
  placeholderImage: string;
  category: CategoryDetails_category;
  products: CategoryDetails_category_products_edges_node[];
  subcategories: CategoryDetails_category_children_edges_node[];
  pageInfo: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  saveButtonBarState: ConfirmButtonTransitionState;
  onImageDelete: () => void;
  onSubmit: (data: FormData) => void;
  onImageUpload(event: React.ChangeEvent<any>);
  onNextPage();
  onPreviousPage();
  onProductClick(id: string): () => void;
  onAddProduct();
  onBack();
  onDelete();
  onAddCategory();
  onCategoryClick(id: string): () => void;
}

const decorate = withStyles({
  tabsBorder: {
    borderBottom: "1px solid #eeeeee"
  }
});

export const CategoryUpdatePage = decorate<CategoryUpdatePageProps>(
  ({
    category,
    classes,
    disabled,
    errors: userErrors,
    pageInfo,
    products,
    saveButtonBarState,
    subcategories,
    onAddCategory,
    onAddProduct,
    onBack,
    onCategoryClick,
    onDelete,
    onNextPage,
    onPreviousPage,
    onProductClick,
    onSubmit
  }) => {
    const initialData = category
      ? {
          description: category.description || "",
          name: category.name,
          seoDescription: category.seoDescription || "",
          seoTitle: category.seoTitle || ""
        }
      : {
          description: "",
          name: "",
          seoDescription: "",
          seoTitle: ""
        };
    return (
      <Form
        onSubmit={onSubmit}
        initial={initialData}
        errors={userErrors}
        key={JSON.stringify(category)}
      >
        {({ data, change, errors, submit, hasChanged }) => (
          <Container width="md">
            <PageHeader
              title={category ? category.name : undefined}
              onBack={onBack}
            />
            <CategoryDetailsForm
              data={data}
              disabled={disabled}
              errors={errors}
              onChange={change}
            />
            <CardSpacer />
            {/* TODO: Uncomment this section after API fixes */}
            {/* <CategoryBackground
              onImageUpload={onImageUpload}
              onImageDelete={onImageDelete}
              backgroundImage={maybe(() => category.backgroundImage)}
              placeholderImage={placeholderImage}
            /> */}
            <CardSpacer />
            <SeoForm
              helperText={i18n.t(
                "Add search engine title and description to make this category easier to find"
              )}
              title={data.seoTitle}
              titlePlaceholder={data.name}
              description={data.seoDescription}
              descriptionPlaceholder={data.description}
              loading={!category}
              onChange={change}
              disabled={disabled}
            />
            <CardSpacer />
            <Tabs>
              {({ changeTab, currentTab }) => (
                <>
                  <div className={classes.tabsBorder}>
                    <Tab
                      isActive={currentTab === 0}
                      value={0}
                      changeTab={changeTab}
                    >
                      {i18n.t("Subcategories")}
                    </Tab>
                    <Tab
                      isActive={currentTab === 1}
                      value={1}
                      changeTab={changeTab}
                    >
                      {i18n.t("Products")}
                    </Tab>
                  </div>
                  <CardSpacer />
                  {currentTab === 0 && (
                    <CategoryList
                      isRoot={false}
                      categories={subcategories}
                      onAdd={onAddCategory}
                      onRowClick={onCategoryClick}
                    />
                  )}
                  {currentTab === 1 && (
                    <CategoryProductsCard
                      categoryName={maybe(() => category.name)}
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
              onDelete={onDelete}
              onSave={submit}
              labels={{
                delete: i18n.t("Delete category")
              }}
              state={saveButtonBarState}
              disabled={disabled || !hasChanged}
            />
          </Container>
        )}
      </Form>
    );
  }
);
CategoryUpdatePage.displayName = "CategoryUpdatePage";
export default CategoryUpdatePage;
