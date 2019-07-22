import React from "react";

import useNavigator from "@saleor/hooks/useNavigator";
import { configurationMenuUrl } from "../../configuration";
import { maybe } from "../../misc";
import CountryListPage from "../components/CountryListPage";
import { TypedFetchTaxes, TypedUpdateTaxSettings } from "../mutations";
import { TypedCountryListQuery } from "../queries";
import { countryTaxRatesUrl } from "../urls";

export const CountryList: React.StatelessComponent = () => {
  const navigate = useNavigator();

  return (
    <TypedUpdateTaxSettings>
      {(updateTaxSettings, updateTaxSettingsOpts) => (
        <TypedFetchTaxes>
          {(fetchTaxes, fetchTaxesOpts) => (
            <TypedCountryListQuery displayLoader={true}>
              {({ data, loading }) => (
                <CountryListPage
                  disabled={
                    loading ||
                    fetchTaxesOpts.loading ||
                    updateTaxSettingsOpts.loading
                  }
                  onBack={() => navigate(configurationMenuUrl)}
                  onRowClick={code => navigate(countryTaxRatesUrl(code))}
                  onSubmit={formData =>
                    updateTaxSettings({
                      variables: {
                        input: {
                          chargeTaxesOnShipping: formData.chargeTaxesOnShipping,
                          displayGrossPrices: formData.showGross,
                          includeTaxesInPrices: formData.includeTax
                        }
                      }
                    })
                  }
                  onTaxFetch={fetchTaxes}
                  shop={maybe(() => ({
                    ...data.shop,
                    countries: data.shop.countries.filter(
                      country => country.vat
                    )
                  }))}
                />
              )}
            </TypedCountryListQuery>
          )}
        </TypedFetchTaxes>
      )}
    </TypedUpdateTaxSettings>
  );
};
export default CountryList;
