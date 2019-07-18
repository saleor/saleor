/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeUpdateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeUpdate
// ====================================================

export interface AttributeUpdate_attributeUpdate_errors {
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

export interface AttributeUpdate_attributeUpdate_attribute_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface AttributeUpdate_attributeUpdate_attribute {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of an attribute name.
   */
  slug: string | null;
  /**
   * List of attribute's values.
   */
  values: (AttributeUpdate_attributeUpdate_attribute_values | null)[] | null;
}

export interface AttributeUpdate_attributeUpdate {
  __typename: "AttributeUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: AttributeUpdate_attributeUpdate_errors[] | null;
  attribute: AttributeUpdate_attributeUpdate_attribute | null;
}

export interface AttributeUpdate {
  /**
   * Updates attribute.
   */
  attributeUpdate: AttributeUpdate_attributeUpdate | null;
}

export interface AttributeUpdateVariables {
  id: string;
  input: AttributeUpdateInput;
}
