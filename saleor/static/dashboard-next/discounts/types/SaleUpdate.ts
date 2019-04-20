/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { SaleInput, SaleType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SaleUpdate
// ====================================================

export interface SaleUpdate_saleUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface SaleUpdate_saleUpdate_sale {
  __typename: "Sale";
  id: string;
  name: string;
  type: SaleType;
  startDate: any;
  endDate: any | null;
  value: number;
}

export interface SaleUpdate_saleUpdate {
  __typename: "SaleUpdate";
  errors: SaleUpdate_saleUpdate_errors[] | null;
  sale: SaleUpdate_saleUpdate_sale | null;
}

export interface SaleUpdate {
  saleUpdate: SaleUpdate_saleUpdate | null;
}

export interface SaleUpdateVariables {
  input: SaleInput;
  id: string;
}
