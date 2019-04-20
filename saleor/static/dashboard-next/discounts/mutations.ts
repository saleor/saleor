import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import {
  saleDetailsFragment,
  saleFragment,
  voucherDetailsFragment,
  voucherFragment
} from "./queries";
import {
  SaleBulkDelete,
  SaleBulkDeleteVariables
} from "./types/SaleBulkDelete";
import {
  SaleCataloguesAdd,
  SaleCataloguesAddVariables
} from "./types/SaleCataloguesAdd";
import {
  SaleCataloguesRemove,
  SaleCataloguesRemoveVariables
} from "./types/SaleCataloguesRemove";
import { SaleCreate, SaleCreateVariables } from "./types/SaleCreate";
import { SaleDelete, SaleDeleteVariables } from "./types/SaleDelete";
import { SaleUpdate, SaleUpdateVariables } from "./types/SaleUpdate";
import {
  VoucherBulkDelete,
  VoucherBulkDeleteVariables
} from "./types/VoucherBulkDelete";
import {
  VoucherCataloguesAdd,
  VoucherCataloguesAddVariables
} from "./types/VoucherCataloguesAdd";
import {
  VoucherCataloguesRemove,
  VoucherCataloguesRemoveVariables
} from "./types/VoucherCataloguesRemove";
import { VoucherCreate, VoucherCreateVariables } from "./types/VoucherCreate";
import { VoucherDelete, VoucherDeleteVariables } from "./types/VoucherDelete";
import { VoucherUpdate, VoucherUpdateVariables } from "./types/VoucherUpdate";

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

const saleCataloguesAdd = gql`
  ${saleDetailsFragment}
  mutation SaleCataloguesAdd(
    $input: CatalogueInput!
    $id: ID!
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    saleCataloguesAdd(id: $id, input: $input) {
      errors {
        field
        message
      }
      sale {
        ...SaleDetailsFragment
      }
    }
  }
`;
export const TypedSaleCataloguesAdd = TypedMutation<
  SaleCataloguesAdd,
  SaleCataloguesAddVariables
>(saleCataloguesAdd);

const saleCataloguesRemove = gql`
  ${saleDetailsFragment}
  mutation SaleCataloguesRemove(
    $input: CatalogueInput!
    $id: ID!
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    saleCataloguesRemove(id: $id, input: $input) {
      errors {
        field
        message
      }
      sale {
        ...SaleDetailsFragment
      }
    }
  }
`;
export const TypedSaleCataloguesRemove = TypedMutation<
  SaleCataloguesRemove,
  SaleCataloguesRemoveVariables
>(saleCataloguesRemove);

const saleCreate = gql`
  ${saleFragment}
  mutation SaleCreate($input: SaleInput!) {
    saleCreate(input: $input) {
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
export const TypedSaleCreate = TypedMutation<SaleCreate, SaleCreateVariables>(
  saleCreate
);

const saleDelete = gql`
  mutation SaleDelete($id: ID!) {
    saleDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedSaleDelete = TypedMutation<SaleDelete, SaleDeleteVariables>(
  saleDelete
);

const saleBulkDelete = gql`
  mutation SaleBulkDelete($ids: [ID]!) {
    saleBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedSaleBulkDelete = TypedMutation<
  SaleBulkDelete,
  SaleBulkDeleteVariables
>(saleBulkDelete);

const voucherUpdate = gql`
  ${voucherFragment}
  mutation VoucherUpdate($input: VoucherInput!, $id: ID!) {
    voucherUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      voucher {
        ...VoucherFragment
      }
    }
  }
`;
export const TypedVoucherUpdate = TypedMutation<
  VoucherUpdate,
  VoucherUpdateVariables
>(voucherUpdate);

const voucherCataloguesAdd = gql`
  ${voucherDetailsFragment}
  mutation VoucherCataloguesAdd(
    $input: CatalogueInput!
    $id: ID!
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    voucherCataloguesAdd(id: $id, input: $input) {
      errors {
        field
        message
      }
      voucher {
        ...VoucherDetailsFragment
      }
    }
  }
`;
export const TypedVoucherCataloguesAdd = TypedMutation<
  VoucherCataloguesAdd,
  VoucherCataloguesAddVariables
>(voucherCataloguesAdd);

const voucherCataloguesRemove = gql`
  ${voucherDetailsFragment}
  mutation VoucherCataloguesRemove(
    $input: CatalogueInput!
    $id: ID!
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    voucherCataloguesRemove(id: $id, input: $input) {
      errors {
        field
        message
      }
      voucher {
        ...VoucherDetailsFragment
      }
    }
  }
`;
export const TypedVoucherCataloguesRemove = TypedMutation<
  VoucherCataloguesRemove,
  VoucherCataloguesRemoveVariables
>(voucherCataloguesRemove);

const voucherCreate = gql`
  ${voucherFragment}
  mutation VoucherCreate($input: VoucherInput!) {
    voucherCreate(input: $input) {
      errors {
        field
        message
      }
      voucher {
        ...VoucherFragment
      }
    }
  }
`;
export const TypedVoucherCreate = TypedMutation<
  VoucherCreate,
  VoucherCreateVariables
>(voucherCreate);

const voucherDelete = gql`
  mutation VoucherDelete($id: ID!) {
    voucherDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedVoucherDelete = TypedMutation<
  VoucherDelete,
  VoucherDeleteVariables
>(voucherDelete);

const voucherBulkDelete = gql`
  mutation VoucherBulkDelete($ids: [ID]!) {
    voucherBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedVoucherBulkDelete = TypedMutation<
  VoucherBulkDelete,
  VoucherBulkDeleteVariables
>(voucherBulkDelete);
