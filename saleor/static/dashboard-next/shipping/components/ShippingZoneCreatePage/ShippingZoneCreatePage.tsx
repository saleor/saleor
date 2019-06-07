import * as React from "react";

import AppHeader from "@saleor-components/AppHeader";
import CardSpacer from "@saleor-components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor-components/ConfirmButton";
import Container from "@saleor-components/Container";
import CountryList from "@saleor-components/CountryList";
import Form from "@saleor-components/Form";
import Grid from "@saleor-components/Grid";
import PageHeader from "@saleor-components/PageHeader";
import SaveButtonBar from "@saleor-components/SaveButtonBar";
import i18n from "../../../i18n";
import { CountryFragment } from "../../../taxes/types/CountryFragment";
import { UserError } from "../../../types";
import ShippingZoneCountriesAssignDialog from "../ShippingZoneCountriesAssignDialog";
import ShippingZoneInfo from "../ShippingZoneInfo";

export interface FormData {
  countries: string[];
  default: boolean;
  name: string;
}

export interface ShippingZoneCreatePageProps {
  countries: CountryFragment[];
  disabled: boolean;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: FormData) => void;
}

const ShippingZoneCreatePage: React.StatelessComponent<
  ShippingZoneCreatePageProps
> = ({ countries, disabled, errors, onBack, onSubmit, saveButtonBarState }) => {
  const [isModalOpened, setModalStatus] = React.useState(false);
  const toggleModal = () => setModalStatus(!isModalOpened);

  const initialForm: FormData = {
    countries: [],
    default: false,
    name: ""
  };

  return (
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <>
          <Container>
            <AppHeader onBack={onBack}>{i18n.t("Shipping")}</AppHeader>
            <PageHeader title={i18n.t("Create New Shipping Zone")} />
            <Grid>
              <div>
                <ShippingZoneInfo
                  data={data}
                  errors={formErrors}
                  onChange={change}
                />
                <CardSpacer />
                <CountryList
                  countries={data.countries.map(selectedCountry =>
                    countries.find(country => country.code === selectedCountry)
                  )}
                  disabled={disabled}
                  emptyText={
                    data.default
                      ? i18n.t(
                          "This is default shipping zone, which means that it covers all of the countries which are not assigned to other shipping zones"
                        )
                      : i18n.t(
                          "Currently, there are no countries assigned to this shipping zone"
                        )
                  }
                  onCountryAssign={toggleModal}
                  onCountryUnassign={countryCode =>
                    change({
                      target: {
                        name: "countries",
                        value: data.countries.filter(
                          country => country !== countryCode
                        )
                      }
                    } as any)
                  }
                  title={i18n.t("Countries")}
                />
              </div>
            </Grid>
            <SaveButtonBar
              disabled={disabled || !hasChanged}
              onCancel={onBack}
              onSave={submit}
              state={saveButtonBarState}
            />
          </Container>
          <ShippingZoneCountriesAssignDialog
            open={isModalOpened}
            onConfirm={formData =>
              change(
                {
                  target: {
                    name: "default",
                    value: formData.restOfTheWorld
                  }
                } as any,
                () =>
                  change(
                    {
                      target: {
                        name: "countries",
                        value: formData.restOfTheWorld ? [] : formData.countries
                      }
                    } as any,
                    toggleModal
                  )
              )
            }
            confirmButtonState="default"
            countries={countries}
            initial={data.countries}
            isDefault={data.default}
            onClose={toggleModal}
          />
        </>
      )}
    </Form>
  );
};
ShippingZoneCreatePage.displayName = "ShippingZoneCreatePage";
export default ShippingZoneCreatePage;
