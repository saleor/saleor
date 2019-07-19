import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import { ChangeEvent, FormChange } from "@saleor/hooks/useForm";
import useStateFromProps from "@saleor/hooks/useStateFromProps";
import { ProductTypeDetails_taxTypes } from "@saleor/productTypes/types/ProductTypeDetails";
import { UserError } from "@saleor/types";
import i18n from "../../../i18n";
import { WeightUnitsEnum } from "../../../types/globalTypes";
import ProductTypeDetails from "../ProductTypeDetails/ProductTypeDetails";
import ProductTypeShipping from "../ProductTypeShipping/ProductTypeShipping";
import ProductTypeTaxes from "../ProductTypeTaxes/ProductTypeTaxes";

export interface ProductTypeForm {
  name: string;
  isShippingRequired: boolean;
  taxType: string;
  weight: number;
}

export interface ProductTypeCreatePageProps {
  errors: UserError[];
  defaultWeightUnit: WeightUnitsEnum;
  disabled: boolean;
  pageTitle: string;
  saveButtonBarState: ConfirmButtonTransitionState;
  taxTypes: ProductTypeDetails_taxTypes[];
  onBack: () => void;
  onSubmit: (data: ProductTypeForm) => void;
}

const formInitialData: ProductTypeForm = {
  isShippingRequired: false,
  name: "",
  taxType: "",
  weight: 0
};

function handleTaxTypeChange(
  event: ChangeEvent,
  taxTypes: ProductTypeDetails_taxTypes[],
  formChange: FormChange,
  displayChange: (name: string) => void
) {
  formChange(event);
  displayChange(
    taxTypes.find(taxType => taxType.taxCode === event.target.value).description
  );
}

const ProductTypeCreatePage: React.StatelessComponent<
  ProductTypeCreatePageProps
> = ({
  defaultWeightUnit,
  disabled,
  errors,
  pageTitle,
  saveButtonBarState,
  taxTypes,
  onBack,
  onSubmit
}: ProductTypeCreatePageProps) => {
  const [taxTypeDisplayName, setTaxTypeDisplayName] = useStateFromProps("");

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
              <CardSpacer />
              <ProductTypeTaxes
                disabled={disabled}
                data={data}
                taxTypes={taxTypes}
                taxTypeDisplayName={taxTypeDisplayName}
                onChange={event =>
                  handleTaxTypeChange(
                    event,
                    taxTypes,
                    change,
                    setTaxTypeDisplayName
                  )
                }
              />
            </div>
            <div>
              <ProductTypeShipping
                disabled={disabled}
                data={data}
                defaultWeightUnit={defaultWeightUnit}
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
