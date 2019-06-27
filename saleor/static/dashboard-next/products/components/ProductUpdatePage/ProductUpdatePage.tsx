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
import i18n from "@saleor/i18n";
import { maybe } from "@saleor/misc";
import { ListActions, UserError } from "@saleor/types";
import {
  ProductDetails_product,
  ProductDetails_product_collections,
  ProductDetails_product_images,
  ProductDetails_product_variants
} from "../../types/ProductDetails";
import ProductAttributes, {
  ProductAttributeInput,
  ProductAttributeInputData
} from "../ProductAttributes";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductImages from "../ProductImages";
import ProductOrganization from "../ProductOrganization";
import ProductPricing from "../ProductPricing";
import ProductStock from "../ProductStock";
import ProductVariants from "../ProductVariants";

interface Collection {
  id: string;
  label: string;
}

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

export interface FormData {
  basePrice: number;
  category: string | null;
  chargeTaxes: boolean;
  collections: string[];
  description: RawDraftContentState;
  isPublished: boolean;
  name: string;
  publicationDate: string;
  seoDescription: string;
  seoTitle: string;
  sku: string;
  stockQuantity: number;
}
export interface ProductUpdatePageSubmitData extends FormData {
  attributes: ProductAttributeInput[];
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
  const { change: changeAttributeData, data: attributes } = useFormset<
    ProductAttributeInputData
  >(
    maybe(
      (): ProductAttributeInput[] =>
        product.attributes.map(attribute => ({
          data: {
            inputType: attribute.attribute.inputType,
            values: attribute.attribute.values
          },
          id: attribute.attribute.id,
          label: attribute.attribute.name,
          value: attribute.value.slug
        })),
      []
    )
  );
  const [selectedCategory, setSelectedCategory] = React.useState("");
  const [selectedCollections, setSelectedCollections] = React.useState<
    Collection[]
  >(
    maybe(
      () =>
        productCollections.map(collection => ({
          id: collection.id,
          label: collection.name
        })),
      []
    )
  );

  const initialDescription = maybe<RawDraftContentState>(() =>
    JSON.parse(product.descriptionJson)
  );

  const initialData: FormData = {
    basePrice: maybe(() => product.basePrice.amount, 0),
    category: maybe(() => product.category.id),
    chargeTaxes: maybe(() => product.chargeTaxes, false),
    collections: productCollections
      ? productCollections.map(collection => collection.id)
      : [],
    description: initialDescription,
    isPublished: maybe(() => product.isPublished, false),
    name: maybe(() => product.name, ""),
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
  const categories = maybe(
    () =>
      categoryChoiceList.map(collection => ({
        label: collection.name,
        value: collection.id
      })),
    []
  );
  const collections = maybe(
    () =>
      collectionChoiceList.map(collection => ({
        label: collection.name,
        value: collection.id
      })),
    []
  );
  const currency = maybe(() => product.basePrice.currency);
  const hasVariants = maybe(() => product.productType.hasVariants, false);

  const handleSubmit = (data: FormData) =>
    onSubmit({
      attributes,
      ...data
    });

  return (
    <Form
      onSubmit={handleSubmit}
      errors={userErrors}
      initial={initialData}
      confirmLeave
    >
      {({ change, data, errors, hasChanged, submit }) => {
        const handleCollectionSelect = (event: React.ChangeEvent<any>) => {
          const id = event.target.value;
          const collectionIndex = data.collections.indexOf(id);
          const collectionList =
            collectionIndex === -1
              ? [
                  ...selectedCollections,
                  {
                    id,
                    label: collections.find(
                      collection => collection.value === id
                    ).label
                  }
                ]
              : [
                  ...selectedCollections.slice(0, collectionIndex),
                  ...selectedCollections.slice(collectionIndex + 1)
                ];

          setSelectedCollections(collectionList);
          change({
            target: {
              name: "collections",
              value: collectionList.map(collection => collection.id)
            }
          } as any);
        };

        const handleCategorySelect = (event: React.ChangeEvent<any>) => {
          const id = event.target.value;
          setSelectedCategory(
            categoryChoiceList.find(category => category.id === id).name
          );
          change(event);
        };

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
                    onChange={changeAttributeData}
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
                    collectionInputDisplayValue={selectedCollections
                      .map(c => c.label)
                      .join(", ")}
                    errors={errors}
                    fetchCategories={fetchCategories}
                    fetchCollections={fetchCollections}
                    collections={collections}
                    productType={maybe(() => product.productType)}
                    data={data}
                    disabled={disabled}
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
