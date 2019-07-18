/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { SaleInput, SaleType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SaleCreate
// ====================================================

export interface SaleCreate_saleCreate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface SaleCreate_saleCreate_sale {
  __typename: "Sale";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  type: SaleType;
  startDate: any;
  endDate: any | null;
  value: number;
}

export interface SaleCreate_saleCreate {
  __typename: "SaleCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: SaleCreate_saleCreate_errors[] | null;
  sale: SaleCreate_saleCreate_sale | null;
}

export interface SaleCreate {
  /**
   * Creates a new sale.
   */
  saleCreate: SaleCreate_saleCreate | null;
}

export interface SaleCreateVariables {
  input: SaleInput;
}
