import * as React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { ProductVariantCreateData_product } from "../../types/ProductVariantCreateData";
import ProductVariantAttributes from "../ProductVariantAttributes";
import ProductVariantNavigation from "../ProductVariantNavigation";
import ProductVariantPrice from "../ProductVariantPrice";
import ProductVariantStock from "../ProductVariantStock";

interface FormData {
  attributes?: Array<{
    slug: string;
    value: string;
  }>;
  costPrice?: string;
  images?: string[];
  priceOverride?: string;
  quantity?: number;
  sku?: string;
}

interface ProductVariantCreatePageProps {
  currencySymbol: string;
  errors: UserError[];
  header: string;
  loading: boolean;
  product: ProductVariantCreateData_product;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: FormData) => void;
  onVariantClick: (variantId: string) => void;
}

const ProductVariantCreatePage: React.StatelessComponent<
  ProductVariantCreatePageProps
> = ({
  currencySymbol,
  errors: formErrors,
  loading,
  header,
  product,
  saveButtonBarState,
  onBack,
  onSubmit,
  onVariantClick
}) => {
  const initialForm = {
    attributes: maybe(() =>
      product.productType.variantAttributes.map(attribute => ({
        slug: attribute.slug,
        value: ""
      }))
    ),
    costPrice: "",
    images: maybe(() => product.images.map(image => image.id)),
    priceOverride: "",
    quantity: 0,
    sku: ""
  };
  return (
    <Form initial={initialForm} errors={formErrors} onSubmit={onSubmit}>
      {({ change, data, errors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{maybe(() => product.name)}</AppHeader>
          <PageHeader title={header} />
          <Grid variant="inverted">
            <div>
              <ProductVariantNavigation
                fallbackThumbnail={maybe(() => product.thumbnail.url)}
                variants={maybe(() => product.variants)}
                onRowClick={(variantId: string) => {
                  if (product && product.variants) {
                    return onVariantClick(variantId);
                  }
                }}
              />
            </div>
            <div>
              <ProductVariantAttributes
                attributes={maybe(() => product.productType.variantAttributes)}
                data={data}
                disabled={loading}
                onChange={change}
              />
              <CardSpacer />
              <ProductVariantPrice
                errors={errors}
                priceOverride={data.priceOverride}
                currencySymbol={currencySymbol}
                costPrice={data.costPrice}
                loading={loading}
                onChange={change}
              />
              <CardSpacer />
              <ProductVariantStock
                errors={errors}
                sku={data.sku}
                quantity={data.quantity}
                loading={loading}
                onChange={change}
              />
            </div>
          </Grid>
          <SaveButtonBar
            disabled={loading || !onSubmit || !hasChanged}
            labels={{
              delete: i18n.t("Remove variant"),
              save: i18n.t("Save variant")
            }}
            state={saveButtonBarState}
            onCancel={onBack}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  );
};
ProductVariantCreatePage.displayName = "ProductVariantCreatePage";
export default ProductVariantCreatePage;
