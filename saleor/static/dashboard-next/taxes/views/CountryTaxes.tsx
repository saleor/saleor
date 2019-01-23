import * as React from "react";

import Navigator from "../../components/Navigator";
import { maybe } from "../../misc";
import CountryTaxesPage from "../components/CountryTaxesPage";
import { TypedCountryListQuery } from "../queries";
import { countryListUrl } from "../urls";

export interface CountryTaxesParams {
  code: string;
}

export const CountryTaxes: React.StatelessComponent<CountryTaxesParams> = ({
  code
}) => (
  <Navigator>
    {navigate => (
      <TypedCountryListQuery displayLoader={true}>
        {({ data }) => {
          const country = maybe(() =>
            data.shop.countries.find(country => country.code === code)
          );
          return (
            <CountryTaxesPage
              countryName={maybe(() => country.country)}
              taxCategories={maybe(() => country.vat.reducedRates)}
              onBack={() => navigate(countryListUrl)}
            />
          );
        }}
      </TypedCountryListQuery>
    )}
  </Navigator>
);
export default CountryTaxes;
