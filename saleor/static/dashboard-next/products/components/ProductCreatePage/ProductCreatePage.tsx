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
import useFormset from "@saleor/hooks/useFormset";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { ProductCreateData_productTypes_edges_node_productAttributes } from "../../types/ProductCreateData";
import ProductAttributes, {
  ProductAttributeInput,
  ProductAttributeInputData
} from "../ProductAttributes";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductOrganization from "../ProductOrganization";
import ProductPricing from "../ProductPricing";
import ProductStock from "../ProductStock";

interface Collection {
  id: string;
  label: string;
}
interface ProductType {
  hasVariants: boolean;
  id: string;
  name: string;
  productAttributes: ProductCreateData_productTypes_edges_node_productAttributes[];
}
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
  collections?: Array<{
    id: string;
    name: string;
  }>;
  currency: string;
  categories?: Array<{
    id: string;
    name: string;
  }>;
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
  const { change: changeAttributeData, data: attributes } = useFormset<
    ProductAttributeInputData
  >(
    productType.productAttributes.map(attribute => ({
      data: {
        inputType: attribute.inputType,
        values: attribute.values
      },
      id: attribute.id,
      label: attribute.name,
      value: ""
    }))
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
  const productTypes = maybe(
    () =>
      productTypeChoiceList.map(pt => ({
        label: pt.name,
        value: pt.id
      })),
    []
  );

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
                    label: collectionChoiceList.find(
                      collection => collection.id === id
                    ).name
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

        const handleProductTypeChange = (event: React.ChangeEvent<any>) => {
          const id = event.target.value;
          const selectedProductType = productTypeChoiceList.find(
            productType => productType.id === id
          );
          setProductType(selectedProductType);
          change(event);
          change({
            target: {
              name: "attributes",
              value: selectedProductType.productAttributes.map(attribute => ({
                slug: attribute.slug,
                value: ""
              }))
            }
          } as any);
        };

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
                  onProductTypeChange={handleProductTypeChange}
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
