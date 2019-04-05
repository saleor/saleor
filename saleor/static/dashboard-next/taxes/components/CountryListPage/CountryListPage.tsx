import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CountryList_shop } from "../../types/CountryList";
import CountryList from "../CountryList";
import TaxConfiguration from "../TaxConfiguration";

export interface FormData {
  includeTax: boolean;
  showGross: boolean;
  chargeTaxesOnShipping: boolean;
}
export interface CountryListPageProps {
  disabled: boolean;
  shop: CountryList_shop;
  onBack: () => void;
  onRowClick: (code: string) => void;
  onSubmit: (data: FormData) => void;
  onTaxFetch: () => void;
}

const CountryListPage: React.StatelessComponent<CountryListPageProps> = ({
  disabled,
  shop,
  onBack,
  onRowClick,
  onSubmit,
  onTaxFetch
}) => {
  const initialForm: FormData = {
    chargeTaxesOnShipping: maybe(() => shop.chargeTaxesOnShipping, false),
    includeTax: maybe(() => shop.includeTaxesInPrices, false),
    showGross: maybe(() => shop.displayGrossPrices, false)
  };
  return (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Configuration")}</AppHeader>
          <PageHeader title={i18n.t("Taxes", { context: "page title" })} />
          <Grid>
            <div>
              <CountryList
                countries={maybe(() => shop.countries)}
                onRowClick={onRowClick}
              />
            </div>
            <div>
              <TaxConfiguration
                data={data}
                disabled={disabled}
                onChange={event => change(event, submit)}
                onTaxFetch={onTaxFetch}
              />
            </div>
          </Grid>
        </Container>
      )}
    </Form>
  );
};
CountryListPage.displayName = "CountryListPage";
export default CountryListPage;
