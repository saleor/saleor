import * as React from "react";

import AppHeader from "../../../components/AppHeader";
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
import { UserError } from "../../../types";
import { ShippingMethodTypeEnum } from "../../../types/globalTypes";
import { ShippingZoneDetailsFragment } from "../../types/ShippingZoneDetailsFragment";
import ShippingZoneInfo from "../ShippingZoneInfo";
import ShippingZoneRates from "../ShippingZoneRates";

export interface FormData {
  name: string;
}

export interface ShippingZoneDetailsPageProps {
  disabled: boolean;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  shippingZone: ShippingZoneDetailsFragment;
  onBack: () => void;
  onCountryAdd: () => void;
  onCountryRemove: (code: string) => void;
  onDelete: () => void;
  onPriceRateAdd: () => void;
  onPriceRateEdit: (id: string) => void;
  onRateRemove: (rateId: string) => void;
  onSubmit: (data: FormData) => void;
  onWeightRateAdd: () => void;
  onWeightRateEdit: (id: string) => void;
}

const ShippingZoneDetailsPage: React.StatelessComponent<
  ShippingZoneDetailsPageProps
> = ({
  disabled,
  errors,
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
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Shipping")}</AppHeader>
          <PageHeader title={maybe(() => shippingZone.name)} />
          <Grid>
            <div>
              <ShippingZoneInfo
                data={data}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <CountryList
                countries={maybe(() => shippingZone.countries)}
                disabled={disabled}
                emptyText={maybe(
                  () =>
                    shippingZone.default
                      ? i18n.t(
                          "This is default shipping zone, which means that it covers all of the countries which are not assigned to other shipping zones"
                        )
                      : i18n.t(
                          "Currently, there are no countries assigned to this shipping zone"
                        ),
                  "..."
                )}
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
