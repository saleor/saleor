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
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ListActions, UserError } from "../../../types";
import {
  ProductDetails_product,
  ProductDetails_product_attributes_attribute,
  ProductDetails_product_images,
  ProductDetails_product_variants
} from "../../types/ProductDetails";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductImages from "../ProductImages";
import ProductOrganization from "../ProductOrganization";
import ProductPricing from "../ProductPricing";
import ProductStock from "../ProductStock";
import ProductVariants from "../ProductVariants";

interface ProductUpdateProps extends ListActions {
  errors: UserError[];
  placeholderImage: string;
  collections?: Array<{
    id: string;
    name: string;
  }>;
  categories?: Array<{
    id: string;
    name: string;
  }>;
  disabled?: boolean;
  productCollections?: Array<{
    id: string;
    name: string;
  }>;
  variants: ProductDetails_product_variants[];
  images?: ProductDetails_product_images[];
  product?: ProductDetails_product;
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
  onSubmit?(data: any);
  onVariantAdd?();
}

interface ChoiceType {
  label: string;
  value: string;
}
export interface FormData {
  attributes: Array<{
    slug: string;
    value: string;
  }>;
  basePrice: number;
  category: ChoiceType | null;
  chargeTaxes: boolean;
  collections: ChoiceType[];
  description: RawDraftContentState;
  isPublished: boolean;
  name: string;
  productType: {
    label: string;
    value: {
      hasVariants: boolean;
      id: string;
      name: string;
      productAttributes: Array<
        Exclude<ProductDetails_product_attributes_attribute, "__typename">
      >;
    };
  } | null;
  publicationDate: string;
  seoDescription: string;
  seoTitle: string;
  sku: string;
  stockQuantity: number;
}

export const ProductUpdate: React.StatelessComponent<ProductUpdateProps> = ({
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
  const initialDescription = maybe<RawDraftContentState>(() =>
    JSON.parse(product.descriptionJson)
  );

  const initialData: FormData = {
    attributes: maybe(
      () =>
        product.attributes.map(a => ({
          slug: a.attribute.slug,
          value: a.value ? a.value.slug : null
        })),
      []
    ),
    basePrice: maybe(() => product.basePrice.amount, 0),
    category: {
      label: maybe(() => product.category.name, ""),
      value: maybe(() => product.category.id, "")
    },
    chargeTaxes: maybe(() => product.chargeTaxes, false),
    collections: productCollections
      ? productCollections.map(collection => ({
          label: collection.name,
          value: collection.id
        }))
      : [],
    description: initialDescription,
    isPublished: maybe(() => product.isPublished, false),
    name: maybe(() => product.name, ""),
    productType: maybe(() => ({
      label: product.productType.name,
      value: {
        hasVariants: product.productType.hasVariants,
        id: product.productType.id,
        name: product.productType.name,
        productAttributes: product.attributes.map(a => a.attribute)
      }
    })),
    publicationDate: maybe(() => product.publicationDate, ""),
    seoDescription: maybe(() => product.seoDescription, ""),
    seoTitle: maybe(() => product.seoTitle, ""),
    sku: maybe(() =>
      product.productType.hasVariants
        ? ""
        : variants && variants[0]
        ? variants[0].sku
        : ""
    ),
    stockQuantity: maybe(() =>
      product.productType.hasVariants
        ? 0
        : variants && variants[0]
        ? variants[0].quantity
        : 0
    )
  };
  const categories =
    categoryChoiceList !== undefined
      ? categoryChoiceList.map(category => ({
          label: category.name,
          value: category.id
        }))
      : [];
  const collections =
    collectionChoiceList !== undefined
      ? collectionChoiceList.map(collection => ({
          label: collection.name,
          value: collection.id
        }))
      : [];
  const currency =
    product && product.basePrice ? product.basePrice.currency : undefined;
  const hasVariants =
    product && product.productType && product.productType.hasVariants;

  return (
    <Form
      onSubmit={onSubmit}
      errors={userErrors}
      initial={initialData}
      confirmLeave
    >
      {({ change, data, errors, hasChanged, set, submit }) => (
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
                  errors={errors}
                  fetchCategories={fetchCategories}
                  fetchCollections={fetchCollections}
                  collections={collections}
                  product={product}
                  data={data}
                  disabled={disabled}
                  onChange={change}
                  onSet={set}
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
      )}
    </Form>
  );
};
ProductUpdate.displayName = "ProductUpdate";
export default ProductUpdate;
