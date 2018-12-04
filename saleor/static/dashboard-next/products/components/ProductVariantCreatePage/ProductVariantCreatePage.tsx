import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
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

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "4fr 9fr",
    [theme.breakpoints.down("sm")]: {
      gridGap: `${theme.spacing.unit}px`,
      gridTemplateColumns: "1fr"
    }
  }
}));

const ProductVariantCreatePage = decorate<ProductVariantCreatePageProps>(
  ({
    classes,
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
      <Container width="md">
        <PageHeader title={header} onBack={onBack} />
        <Form
          initial={initialForm}
          errors={formErrors}
          onSubmit={onSubmit}
          key={product ? JSON.stringify(product) : "noproduct"}
        >
          {({ change, data, errors, hasChanged, submit }) => {
            return (
              <>
                <div className={classes.root}>
                  <div>
                    <ProductVariantNavigation
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
                      attributes={maybe(
                        () => product.productType.variantAttributes
                      )}
                      data={data}
                      disabled={loading}
                      onChange={change}
                    />
                    <ProductVariantPrice
                      errors={errors}
                      priceOverride={data.priceOverride}
                      currencySymbol={currencySymbol}
                      costPrice={data.costPrice}
                      loading={loading}
                      onChange={change}
                    />
                    <ProductVariantStock
                      errors={errors}
                      sku={data.sku}
                      quantity={data.quantity}
                      loading={loading}
                      onChange={change}
                    />
                  </div>
                </div>
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
              </>
            );
          }}
        </Form>
      </Container>
    );
  }
);
ProductVariantCreatePage.displayName = "ProductVariantCreatePage";
export default ProductVariantCreatePage;
