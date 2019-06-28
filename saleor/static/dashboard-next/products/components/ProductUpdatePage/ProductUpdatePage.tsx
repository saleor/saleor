import { convertFromRaw, RawDraftContentState } from "draft-js";
import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import SeoForm from "@saleor/components/SeoForm";
import VisibilityCard from "@saleor/components/VisibilityCard";
import { SearchCategories_categories_edges_node } from "@saleor/containers/SearchCategories/types/SearchCategories";
import { SearchCollections_collections_edges_node } from "@saleor/containers/SearchCollections/types/SearchCollections";
import useFormset from "@saleor/hooks/useFormset";
import useMultiAutocomplete from "@saleor/hooks/useMultiAutocomplete";
import useStateFromProps from "@saleor/hooks/useStateFromProps";
import i18n from "@saleor/i18n";
import { maybe } from "@saleor/misc";
import { ListActions, UserError } from "@saleor/types";
import {
  ProductDetails_product,
  ProductDetails_product_collections,
  ProductDetails_product_images,
  ProductDetails_product_variants
} from "../../types/ProductDetails";
import {
  getAttributeInputFromProduct,
  getChoices,
  getProductUpdatePageFormData,
  ProductUpdatePageFormData
} from "../../utils/data";
import {
  createAttributeChangeHandler,
  createCategorySelectHandler,
  createCollectionSelectHandler
} from "../../utils/handlers";
import ProductAttributes, { ProductAttributeInput } from "../ProductAttributes";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductImages from "../ProductImages";
import ProductOrganization from "../ProductOrganization";
import ProductPricing from "../ProductPricing";
import ProductStock from "../ProductStock";
import ProductVariants from "../ProductVariants";

interface ProductUpdatePageProps extends ListActions {
  errors: UserError[];
  placeholderImage: string;
  collections: SearchCollections_collections_edges_node[];
  categories: SearchCategories_categories_edges_node[];
  disabled: boolean;
  productCollections: ProductDetails_product_collections[];
  variants: ProductDetails_product_variants[];
  images: ProductDetails_product_images[];
  product: ProductDetails_product;
  header: string;
  saveButtonBarState: ConfirmButtonTransitionState;
  fetchCategories: (query: string) => void;
  fetchCollections: (query: string) => void;
  onVariantShow: (id: string) => () => void;
  onImageDelete: (id: string) => () => void;
  onAttributesEdit: () => void;
  onBack?();
  onDelete();
  onImageEdit?(id: string);
  onImageReorder?(event: { oldIndex: number; newIndex: number });
  onImageUpload(file: File);
  onProductShow?();
  onSeoClick?();
  onSubmit?(data: ProductUpdatePageSubmitData);
  onVariantAdd?();
}

export interface ProductUpdatePageSubmitData extends ProductUpdatePageFormData {
  attributes: ProductAttributeInput[];
  collections: string[];
}

export const ProductUpdatePage: React.FC<ProductUpdatePageProps> = ({
  disabled,
  categories: categoryChoiceList,
  collections: collectionChoiceList,
  errors: userErrors,
  fetchCategories,
  fetchCollections,
  images,
  header,
  placeholderImage,
  product,
  productCollections,
  saveButtonBarState,
  variants,
  onAttributesEdit,
  onBack,
  onDelete,
  onImageDelete,
  onImageEdit,
  onImageReorder,
  onImageUpload,
  onSeoClick,
  onSubmit,
  onVariantAdd,
  onVariantShow,
  isChecked,
  selected,
  toggle,
  toggleAll,
  toolbar
}) => {
  const { change: changeAttributeData, data: attributes } = useFormset(
    getAttributeInputFromProduct(product)
  );
  const [selectedCategory, setSelectedCategory] = useStateFromProps(
    maybe(() => product.category.name)
  );

  const {
    change: selectCollection,
    data: selectedCollections
  } = useMultiAutocomplete(getChoices(productCollections));

  const initialData = getProductUpdatePageFormData(product, variants);
  const initialDescription = maybe<RawDraftContentState>(() =>
    JSON.parse(product.descriptionJson)
  );

  const categories = getChoices(categoryChoiceList);
  const collections = getChoices(collectionChoiceList);
  const currency = maybe(() => product.basePrice.currency);
  const hasVariants = maybe(() => product.productType.hasVariants, false);

  const handleSubmit = (data: ProductUpdatePageFormData) =>
    onSubmit({
      attributes,
      collections: selectedCollections.map(({ value }) => value),
      ...data
    });

  return (
    <Form
      onSubmit={handleSubmit}
      errors={userErrors}
      initial={initialData}
      confirmLeave
    >
      {({ change, data, errors, hasChanged, submit, triggerChange }) => {
        const handleCollectionSelect = createCollectionSelectHandler(
          event => selectCollection(event, collections),
          triggerChange
        );
        const handleCategorySelect = createCategorySelectHandler(
          categoryChoiceList,
          setSelectedCategory,
          change
        );
        const handleAttributeChange = createAttributeChangeHandler(
          changeAttributeData,
          triggerChange
        );

        return (
          <>
            <Container>
              <AppHeader onBack={onBack}>{i18n.t("Products")}</AppHeader>
              <PageHeader title={header} />
              <Grid>
                <div>
                  <ProductDetailsForm
                    data={data}
                    disabled={disabled}
                    errors={errors}
                    initialDescription={initialDescription}
                    onChange={change}
                  />
                  <CardSpacer />
                  <ProductImages
                    images={images}
                    placeholderImage={placeholderImage}
                    onImageDelete={onImageDelete}
                    onImageReorder={onImageReorder}
                    onImageEdit={onImageEdit}
                    onImageUpload={onImageUpload}
                  />
                  <CardSpacer />
                  <ProductAttributes
                    attributes={attributes}
                    disabled={disabled}
                    onChange={handleAttributeChange}
                  />
                  <CardSpacer />
                  <ProductPricing
                    currency={currency}
                    data={data}
                    disabled={disabled}
                    onChange={change}
                  />
                  <CardSpacer />
                  {hasVariants ? (
                    <ProductVariants
                      disabled={disabled}
                      variants={variants}
                      fallbackPrice={product ? product.basePrice : undefined}
                      onAttributesEdit={onAttributesEdit}
                      onRowClick={onVariantShow}
                      onVariantAdd={onVariantAdd}
                      toolbar={toolbar}
                      isChecked={isChecked}
                      selected={selected}
                      toggle={toggle}
                      toggleAll={toggleAll}
                    />
                  ) : (
                    <ProductStock
                      data={data}
                      disabled={disabled}
                      product={product}
                      onChange={change}
                      errors={errors}
                    />
                  )}
                  <CardSpacer />
                  <SeoForm
                    title={data.seoTitle}
                    titlePlaceholder={data.name}
                    description={data.seoDescription}
                    descriptionPlaceholder={maybe(() =>
                      convertFromRaw(data.description)
                        .getPlainText()
                        .slice(0, 300)
                    )}
                    loading={disabled}
                    onClick={onSeoClick}
                    onChange={change}
                  />
                </div>
                <div>
                  <ProductOrganization
                    canChangeType={false}
                    categories={categories}
                    categoryInputDisplayValue={selectedCategory}
                    collections={collections}
                    data={data}
                    disabled={disabled}
                    errors={errors}
                    fetchCategories={fetchCategories}
                    fetchCollections={fetchCollections}
                    productType={maybe(() => product.productType)}
                    selectedCollections={selectedCollections}
                    onCategoryChange={handleCategorySelect}
                    onCollectionChange={handleCollectionSelect}
                  />
                  <CardSpacer />
                  <VisibilityCard
                    data={data}
                    errors={errors}
                    disabled={disabled}
                    onChange={change}
                  />
                </div>
              </Grid>
              <SaveButtonBar
                onCancel={onBack}
                onDelete={onDelete}
                onSave={submit}
                state={saveButtonBarState}
                disabled={disabled || !hasChanged}
              />
            </Container>
          </>
        );
      }}
    </Form>
  );
};
ProductUpdatePage.displayName = "ProductUpdatePage";
export default ProductUpdatePage;
