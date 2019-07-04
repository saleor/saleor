import gql from "graphql-tag";
import { TypedQuery } from "../queries";
import { CountryList } from "./types/CountryList";

export const countryFragment = gql`
  fragment CountryFragment on CountryDisplay {
    country
    code
  }
`;
export const countryWithTaxesFragment = gql`
  ${countryFragment}
  fragment CountryWithTaxesFragment on CountryDisplay {
    ...CountryFragment
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
  ${countryWithTaxesFragment}
  ${shopTaxesFragment}
  query CountryList {
    shop {
      ...ShopTaxesFragment
      countries {
        ...CountryWithTaxesFragment
      }
    }
  }
`;
export const TypedCountryListQuery = TypedQuery<CountryList, {}>(countryList);
