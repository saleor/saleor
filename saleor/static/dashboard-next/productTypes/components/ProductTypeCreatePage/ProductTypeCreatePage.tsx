import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { TaxRateType, WeightUnitsEnum } from "../../../types/globalTypes";
import ProductTypeDetails from "../ProductTypeDetails/ProductTypeDetails";
import ProductTypeShipping from "../ProductTypeShipping/ProductTypeShipping";
import ProductTypeTaxes from "../ProductTypeTaxes/ProductTypeTaxes";

export interface ProductTypeForm {
  chargeTaxes: boolean;
  name: string;
  isShippingRequired: boolean;
  taxRate: TaxRateType;
  weight: number;
}

export interface ProductTypeCreatePageProps {
  errors: Array<{
    field: string;
    message: string;
  }>;
  defaultWeightUnit: WeightUnitsEnum;
  disabled: boolean;
  pageTitle: string;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: ProductTypeForm) => void;
}

const ProductTypeCreatePage: React.StatelessComponent<
  ProductTypeCreatePageProps
> = ({
  defaultWeightUnit,
  disabled,
  errors,
  pageTitle,
  saveButtonBarState,
  onBack,
  onSubmit
}: ProductTypeCreatePageProps) => {
  const formInitialData: ProductTypeForm = {
    chargeTaxes: true,
    isShippingRequired: false,
    name: "",
    taxRate: TaxRateType.STANDARD,
    weight: 0
  };
  return (
    <Form
      errors={errors}
      initial={formInitialData}
      onSubmit={onSubmit}
      confirmLeave
    >
      {({ change, data, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Product Types")}</AppHeader>
          <PageHeader title={pageTitle} />
          <Grid>
            <div>
              <ProductTypeDetails
                data={data}
                disabled={disabled}
                onChange={change}
              />
            </div>
            <div>
              <ProductTypeShipping
                disabled={disabled}
                data={data}
                defaultWeightUnit={defaultWeightUnit}
                onChange={change}
              />
              <CardSpacer />
              <ProductTypeTaxes
                disabled={disabled}
                data={data}
                onChange={change}
              />
            </div>
          </Grid>
          <SaveButtonBar
            onCancel={onBack}
            onSave={submit}
            disabled={disabled || !hasChanged}
            state={saveButtonBarState}
          />
        </Container>
      )}
    </Form>
  );
};
ProductTypeCreatePage.displayName = "ProductTypeCreatePage";
export default ProductTypeCreatePage;
