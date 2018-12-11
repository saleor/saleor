import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
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

const styles = (theme: Theme) =>
  createStyles({
    cardContainer: {
      marginTop: theme.spacing.unit * 2
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "2fr 1fr"
    }
  });

export interface ProductTypeCreatePageProps extends WithStyles<typeof styles> {
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

const ProductTypeCreatePage = withStyles(styles, {
  name: "ProductTypeCreatePage"
})(
  ({
    classes,
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
          <Container width="md">
            <PageHeader title={pageTitle} onBack={onBack} />
            <div className={classes.root}>
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
                <div className={classes.cardContainer}>
                  <ProductTypeTaxes
                    disabled={disabled}
                    data={data}
                    onChange={change}
                  />
                </div>
              </div>
            </div>
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
  }
);
ProductTypeCreatePage.displayName = "ProductTypeCreatePage";
export default ProductTypeCreatePage;
