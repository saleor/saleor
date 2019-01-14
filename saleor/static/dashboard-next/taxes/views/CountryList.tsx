import * as React from "react";

import Navigator from "../../components/Navigator";
import { maybe } from "../../misc";
import CountryListPage from "../components/CountryListPage";
import { TypedCountryListQuery } from "../queries";
import { countryTaxRatesUrl } from "../urls";

export const CountryList: React.StatelessComponent = () => (
  <Navigator>
    {navigate => (
      <TypedCountryListQuery displayLoader={true}>
        {({ data, loading }) => (
          <CountryListPage
            disabled={loading}
            onRowClick={code => navigate(countryTaxRatesUrl(code))}
            onSubmit={() => undefined}
            onTaxFetch={() => undefined}
            shop={maybe(() => ({
              ...data.shop,
              countries: data.shop.countries.filter(country => country.vat)
            }))}
          />
        )}
      </TypedCountryListQuery>
    )}
  </Navigator>
);
export default CountryList;
