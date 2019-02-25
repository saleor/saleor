import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import CountryList from "../../../components/CountryList";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ShippingMethodTypeEnum } from "../../../types/globalTypes";
import { ShippingZoneDetailsFragment } from "../../types/ShippingZoneDetailsFragment";
import ShippingZoneInfo from "../ShippingZoneInfo";
import ShippingZoneRates from "../ShippingZoneRates";

export interface FormData {
  name: string;
}

export interface ShippingZoneDetailsPageProps {
  disabled: boolean;
  saveButtonBarState: ConfirmButtonTransitionState;
  shippingZone: ShippingZoneDetailsFragment;
  onBack: () => void;
  onCountryAdd: () => void;
  onCountryRemove: (code: string) => void;
  onDelete: () => void;
  onPriceRateAdd: () => void;
  onPriceRateEdit: (id: string) => void;
  onRateRemove: () => void;
  onSubmit: (data: FormData) => void;
  onWeightRateAdd: () => void;
  onWeightRateEdit: (id: string) => void;
}

const ShippingZoneDetailsPage: React.StatelessComponent<
  ShippingZoneDetailsPageProps
> = ({
  disabled,
  onBack,
  onCountryAdd,
  onCountryRemove,
  onDelete,
  onPriceRateAdd,
  onPriceRateEdit,
  onRateRemove,
  onSubmit,
  onWeightRateAdd,
  onWeightRateEdit,
  saveButtonBarState,
  shippingZone
}) => {
  const initialForm: FormData = {
    name: maybe(() => shippingZone.name, "")
  };
  return (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={maybe(() => shippingZone.name)} onBack={onBack} />
          <Grid>
            <div>
              <ShippingZoneInfo data={data} onChange={change} />
              <CardSpacer />
              <CountryList
                countries={maybe(() => shippingZone.countries)}
                disabled={disabled}
                emptyText={i18n.t("Placeholder")}
                onCountryAssign={onCountryAdd}
                onCountryUnassign={onCountryRemove}
                title={i18n.t("Countries")}
              />
              <CardSpacer />
              <ShippingZoneRates
                disabled={disabled}
                onRateAdd={onPriceRateAdd}
                onRateEdit={onPriceRateEdit}
                onRateRemove={onRateRemove}
                rates={maybe(() =>
                  shippingZone.shippingMethods.filter(
                    method => method.type === ShippingMethodTypeEnum.PRICE
                  )
                )}
                variant="price"
              />
              <CardSpacer />
              <ShippingZoneRates
                disabled={disabled}
                onRateAdd={onWeightRateAdd}
                onRateEdit={onWeightRateEdit}
                onRateRemove={onRateRemove}
                rates={maybe(() =>
                  shippingZone.shippingMethods.filter(
                    method => method.type === ShippingMethodTypeEnum.WEIGHT
                  )
                )}
                variant="weight"
              />
            </div>
          </Grid>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onDelete={onDelete}
            onSave={submit}
            state={saveButtonBarState}
          />
        </Container>
      )}
    </Form>
  );
};
ShippingZoneDetailsPage.displayName = "ShippingZoneDetailsPage";
export default ShippingZoneDetailsPage;
