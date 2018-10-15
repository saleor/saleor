import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { UserError } from "../../../";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import Tabs, { Tab } from "../../../components/Tab";
import { MoneyType } from "../../../products";
import CategoryDetailsForm from "../../components/CategoryDetailsForm";
import CategoryList from "../../components/CategoryList";
import CategoryBackground from "../CategoryBackground";
import CategoryProductsCard from "../CategoryProductsCard";

import { CardSpacer } from "../../../components/CardSpacer";
import i18n from "../../../i18n";

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
  category: {
    SeoDescription: string;
    SeoTitle: string;
    name: string;
    description: string;
  };
  backgroundImage?: {
    url?: string;
  };
  products: Array<{
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
  subcategories: Array<{
    id: string;
    name: string;
    children: {
      totalCount: number;
    };
    products: {
      totalCount: number;
    };
  }>;
  pageInfo: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  loading: boolean;
  saveButtonBarState?: SaveButtonBarState;
  onImageDelete: (id: string) => () => void;
  onSubmit(data: FormData);
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
    onAddCategory,
    onCategoryClick,
    onImageDelete,
    placeholderImage,
    backgroundImage
  }) => {
    const initialData = category
      ? {
          description: category.description,
          name: category.name,
          seoDescription: category.SeoDescription,
          seoTitle: category.SeoTitle
        }
      : {
          description: "",
          name: "",
          seoDescription: "",
          seoTitle: ""
        };
    return (
      <Form onSubmit={onSubmit} initial={initialData} errors={userErrors}>
        {({ data, change, errors, submit, hasChanged }) => (
          <Container width="md">
            <PageHeader title={category ? category.name : undefined} />
            <CategoryDetailsForm
              data={data}
              disabled={disabled}
              errors={errors}
              onChange={change}
            />
            <CardSpacer />
            <CategoryBackground
              onImageUpload={onImageUpload}
              onImageDelete={onImageDelete}
              backgroundImage={backgroundImage}
              placeholderImage={placeholderImage}
            />
            <CardSpacer />
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
                      Subcategories
                    </Tab>
                    <Tab
                      isActive={currentTab === 1}
                      value={1}
                      changeTab={changeTab}
                    >
                      Products
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
                      categoryName={category.name}
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
export default CategoryUpdatePage;
