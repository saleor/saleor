import gql from "graphql-tag";
import { TypedQuery } from "../queries";
import { CountryList } from "./types/CountryList";

const countryList = gql`
  query CountryList {
    shop {
      includeTaxesInPrices
      displayGrossPrices
      countries {
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
    }
  }
`;
export const TypedCountryListQuery = TypedQuery<CountryList, {}>(countryList);
