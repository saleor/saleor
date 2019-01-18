import gql from "graphql-tag";
import { TypedQuery } from "../queries";
import { CountryList } from "./types/CountryList";

export const countryFragment = gql`
  fragment CountryFragment on CountryDisplay {
    country
    code
    vat {
      standardRate
      reducedRates {
        rateType
        rate
      }
    }
  }
`;
export const shopTaxesFragment = gql`
  fragment ShopTaxesFragment on Shop {
    chargeTaxesOnShipping
    includeTaxesInPrices
    displayGrossPrices
  }
`;

const countryList = gql`
  ${countryFragment}
  ${shopTaxesFragment}
  query CountryList {
    shop {
      ...ShopTaxesFragment
      countries {
        ...CountryFragment
      }
    }
  }
`;
export const TypedCountryListQuery = TypedQuery<CountryList, {}>(countryList);
