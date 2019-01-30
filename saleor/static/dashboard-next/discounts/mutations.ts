import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { saleFragment } from "./queries";
import { SaleUpdate, SaleUpdateVariables } from "./types/SaleUpdate";

const saleUpdate = gql`
  ${saleFragment}
  mutation SaleUpdate($input: SaleInput!, $id: ID!) {
    saleUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      sale {
        ...SaleFragment
      }
    }
  }
`;
export const TypedSaleUpdate = TypedMutation<SaleUpdate, SaleUpdateVariables>(
  saleUpdate
);
