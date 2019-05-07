import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Form from "../../../components/Form";
import Hr from "../../../components/Hr";
import SingleSelectField from "../../../components/SingleSelectField";
import i18n from "../../../i18n";
import { WeightUnitsEnum } from "../../../types/globalTypes";

export interface FormData {
  unit: WeightUnitsEnum;
}

export interface ShippingWeightUnitFormProps {
  defaultWeightUnit: WeightUnitsEnum;
  disabled: boolean;
  onSubmit: (unit: WeightUnitsEnum) => void;
}

const ShippingWeightUnitForm: React.StatelessComponent<
  ShippingWeightUnitFormProps
> = ({ defaultWeightUnit, disabled, onSubmit }) => {
  const initialForm: FormData = {
    unit: defaultWeightUnit
  };
  return (
    <Form initial={initialForm} onSubmit={formData => onSubmit(formData.unit)}>
      {({ change, data, submit }) => (
        <Card>
          <CardTitle
            title={i18n.t("Configuration", {
              context: "header"
            })}
          />
          <CardContent>
            <SingleSelectField
              disabled={disabled}
              choices={Object.keys(WeightUnitsEnum).map(unit => ({
                label: WeightUnitsEnum[unit],
                value: WeightUnitsEnum[unit]
              }))}
              label={i18n.t("Shipping Weight Unit", {
                context: "input label"
              })}
              hint={i18n.t(
                "This unit will be used as default shipping weight",
                {
                  context: "input help text"
                }
              )}
              name={"unit" as keyof FormData}
              value={data.unit}
              onChange={change}
            />
          </CardContent>
          <Hr />
          <CardActions>
            <Button color="primary" onClick={submit}>
              {i18n.t("Save", {
                context: "button"
              })}
            </Button>
          </CardActions>
        </Card>
      )}
    </Form>
  );
};
ShippingWeightUnitForm.displayName = "ShippingWeightUnitForm";
export default ShippingWeightUnitForm;
