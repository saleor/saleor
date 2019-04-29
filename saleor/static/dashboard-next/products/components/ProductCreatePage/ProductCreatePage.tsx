import { RawDraftContentState } from "draft-js";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { ProductCreateData_productTypes_edges_node_productAttributes } from "../../types/ProductCreateData";
import ProductAvailabilityForm from "../ProductAvailabilityForm";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductOrganization from "../ProductOrganization";
import ProductPricing from "../ProductPricing";
import ProductStock from "../ProductStock";

interface ChoiceType {
  label: string;
  value: string;
}
export interface FormData {
  attributes: Array<{
    slug: string;
    value: string;
  }>;
  available: boolean;
  publicationDate: string;
  category: ChoiceType;
  chargeTaxes: boolean;
  collections: ChoiceType[];
  description: RawDraftContentState;
  name: string;
  price: number;
  productType: {
    label: string;
    value: {
      hasVariants: boolean;
      id: string;
      name: string;
      productAttributes: ProductCreateData_productTypes_edges_node_productAttributes[];
    };
  };
  seoDescription: string;
  seoTitle: string;
  sku: string;
  stockQuantity: number;
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
  onSubmit?(data: FormData);
}

export const ProductCreatePage: React.StatelessComponent<
  ProductCreatePageProps
> = ({
  currency,
  disabled,
  categories,
  collections,
  errors: userErrors,
  fetchCategories,
  fetchCollections,
  header,
  productTypes,
  saveButtonBarState,
  onBack,
  onSubmit
}: ProductCreatePageProps) => {
  const initialData: FormData = {
    attributes: [],
    available: false,
    category: {
      label: "",
      value: ""
    },
    chargeTaxes: false,
    collections: [],
    description: {} as any,
    name: "",
    price: 0,
    productType: {
      label: "",
      value: {
        hasVariants: false,
        id: "",
        name: "",
        productAttributes: [] as ProductCreateData_productTypes_edges_node_productAttributes[]
      }
    },
    publicationDate: "",
    seoDescription: "",
    seoTitle: "",
    sku: null,
    stockQuantity: null
  };

  return (
    <Form
      onSubmit={onSubmit}
      errors={userErrors}
      initial={initialData}
      confirmLeave
    >
      {({ change, data, errors, hasChanged, submit }) => {
        const hasVariants =
          data.productType && data.productType.value.hasVariants;
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
                  onChange={change}
                />
                <CardSpacer />
                <ProductPricing
                  currency={currency}
                  data={data}
                  disabled={disabled}
                  onChange={change}
                />
                <CardSpacer />
                {!hasVariants && (
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
                  categories={maybe(
                    () =>
                      categories.map(category => ({
                        label: category.name,
                        value: category.id
                      })),
                    []
                  )}
                  errors={errors}
                  fetchCategories={fetchCategories}
                  fetchCollections={fetchCollections}
                  collections={maybe(
                    () =>
                      collections.map(collection => ({
                        label: collection.name,
                        value: collection.id
                      })),
                    []
                  )}
                  productTypes={productTypes}
                  data={data}
                  disabled={disabled}
                  onChange={change}
                />
                <CardSpacer />
                <ProductAvailabilityForm
                  data={data}
                  errors={errors}
                  loading={disabled}
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
