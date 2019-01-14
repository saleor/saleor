import gql from "graphql-tag";
import { TypedQuery } from "../queries";
import { CountryList } from "./types/CountryList";

const countryList = gql`
  query CountryList {
    shop {
      countries {
        country
        code
        vat {
          standardRate
          reducedRates {
            rateType
          }
        }
      }
      displayGrossPrices
      includeTaxesInPrices
    }
  }
`;
export const TypedCountryListQuery = TypedQuery<CountryList, {}>(countryList);
