import { ContentState, convertToRaw, RawDraftContentState } from "draft-js";
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
import {
  Collection,
  getAttributeInputFromProductType,
  getChoices,
  ProductType
} from "@saleor/products/utils/data";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import { ProductCreateData_productTypes_edges_node_productAttributes } from "../../types/ProductCreateData";
import {
  createAttributeChangeHandler,
  createCategorySelectHandler,
  createCollectionSelectHandler,
  createProductTypeSelectHandler
} from "../../utils/handlers";
import ProductAttributes, {
  ProductAttributeInput,
  ProductAttributeInputData
} from "../ProductAttributes";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductOrganization from "../ProductOrganization";
import ProductPricing from "../ProductPricing";
import ProductStock from "../ProductStock";

interface FormData {
  basePrice: number;
  publicationDate: string;
  category: string;
  chargeTaxes: boolean;
  collections: string[];
  description: RawDraftContentState;
  isPublished: boolean;
  name: string;
  productType: string;
  seoDescription: string;
  seoTitle: string;
  sku: string;
  stockQuantity: number;
}
export interface ProductCreatePageSubmitData extends FormData {
  attributes: ProductAttributeInput[];
}

interface ProductCreatePageProps {
  errors: UserError[];
  collections: SearchCollections_collections_edges_node[];
  categories: SearchCategories_categories_edges_node[];
  currency: string;
  disabled: boolean;
  productTypes?: Array<{
    id: string;
    name: string;
    hasVariants: boolean;
    productAttributes: ProductCreateData_productTypes_edges_node_productAttributes[];
  }>;
  header: string;
  saveButtonBarState: ConfirmButtonTransitionState;
  fetchCategories: (data: string) => void;
  fetchCollections: (data: string) => void;
  onAttributesEdit: () => void;
  onBack?();
  onSubmit?(data: ProductCreatePageSubmitData);
}

export const ProductCreatePage: React.StatelessComponent<
  ProductCreatePageProps
> = ({
  currency,
  disabled,
  categories: categoryChoiceList,
  collections: collectionChoiceList,
  errors: userErrors,
  fetchCategories,
  fetchCollections,
  header,
  productTypes: productTypeChoiceList,
  saveButtonBarState,
  onBack,
  onSubmit
}: ProductCreatePageProps) => {
  const initialDescription = convertToRaw(ContentState.createFromText(""));

  const [selectedCategory, setSelectedCategory] = React.useState("");
  const [productType, setProductType] = React.useState<ProductType>({
    hasVariants: false,
    id: "",
    name: "",
    productAttributes: [] as ProductCreateData_productTypes_edges_node_productAttributes[]
  });
  const [selectedCollections, setSelectedCollections] = React.useState<
    Collection[]
  >([]);
  const { change: changeAttributeData, data: attributes } = useFormset(
    getAttributeInputFromProductType(productType)
  );
  const initialData: FormData = {
    basePrice: 0,
    category: "",
    chargeTaxes: false,
    collections: [],
    description: {} as any,
    isPublished: false,
    name: "",
    productType: "",
    publicationDate: "",
    seoDescription: "",
    seoTitle: "",
    sku: null,
    stockQuantity: null
  };

  const categories = getChoices(categoryChoiceList);
  const collections = getChoices(collectionChoiceList);
  const productTypes = getChoices(productTypeChoiceList);

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
      {({ change, data, errors, hasChanged, submit, triggerChange }) => {
        const handleCollectionSelect = createCollectionSelectHandler(
          data,
          collections,
          selectedCollections,
          setSelectedCollections,
          change
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

        const handleProductTypeSelect = createProductTypeSelectHandler(
          productTypeChoiceList,
          setProductType,
          change
        );

        return (
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
                {!productType.hasVariants && (
                  <>
                    <ProductStock
                      data={data}
                      disabled={disabled}
                      product={undefined}
                      onChange={change}
                      errors={errors}
                    />
                    <CardSpacer />
                  </>
                )}
                <SeoForm
                  helperText={i18n.t(
                    "Add search engine title and description to make this product easier to find"
                  )}
                  title={data.seoTitle}
                  titlePlaceholder={data.name}
                  description={data.seoDescription}
                  descriptionPlaceholder={data.seoTitle}
                  loading={disabled}
                  onChange={change}
                />
              </div>
              <div>
                <ProductOrganization
                  canChangeType={true}
                  categories={categories}
                  categoryInputDisplayValue={selectedCategory}
                  errors={errors}
                  fetchCategories={fetchCategories}
                  fetchCollections={fetchCollections}
                  collections={collections}
                  productTypeInputDisplayValue={productType.name}
                  productTypes={productTypes}
                  data={data}
                  productType={productType}
                  disabled={disabled}
                  collectionInputDisplayValue={selectedCollections
                    .map(collection => collection.label)
                    .join(", ")}
                  onCategoryChange={handleCategorySelect}
                  onCollectionChange={handleCollectionSelect}
                  onProductTypeChange={handleProductTypeSelect}
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
              onSave={submit}
              state={saveButtonBarState}
              disabled={disabled || !onSubmit || !hasChanged}
            />
          </Container>
        );
      }}
    </Form>
  );
};
ProductCreatePage.displayName = "ProductCreatePage";
export default ProductCreatePage;
