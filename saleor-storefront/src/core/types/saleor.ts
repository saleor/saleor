/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: getCheckout
// ====================================================

export interface getCheckout_checkout_totalPrice_net {
  amount: number;
}

export interface getCheckout_checkout_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface getCheckout_checkout_totalPrice {
  net: getCheckout_checkout_totalPrice_net;
  gross: getCheckout_checkout_totalPrice_gross;
  currency: string;
}

export interface getCheckout_checkout_subtotalPrice_net {
  amount: number;
}

export interface getCheckout_checkout_subtotalPrice_gross {
  amount: number;
  localized: string;
}

export interface getCheckout_checkout_subtotalPrice {
  net: getCheckout_checkout_subtotalPrice_net;
  gross: getCheckout_checkout_subtotalPrice_gross;
  currency: string;
}

export interface getCheckout_checkout_billingAddress_country {
  code: string;
  country: string;
}

export interface getCheckout_checkout_billingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: getCheckout_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface getCheckout_checkout_shippingAddress_country {
  code: string;
  country: string;
}

export interface getCheckout_checkout_shippingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: getCheckout_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface getCheckout_checkout_availableShippingMethods_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface getCheckout_checkout_availableShippingMethods {
  id: string;
  name: string;
  price: getCheckout_checkout_availableShippingMethods_price | null;
}

export interface getCheckout_checkout_shippingMethod_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface getCheckout_checkout_shippingMethod {
  id: string;
  name: string;
  price: getCheckout_checkout_shippingMethod_price | null;
}

export interface getCheckout_checkout_shippingPrice_net {
  amount: number;
}

export interface getCheckout_checkout_shippingPrice_gross {
  amount: number;
  localized: string;
}

export interface getCheckout_checkout_shippingPrice {
  net: getCheckout_checkout_shippingPrice_net;
  gross: getCheckout_checkout_shippingPrice_gross;
  currency: string;
}

export interface getCheckout_checkout_lines_totalPrice_net {
  amount: number;
}

export interface getCheckout_checkout_lines_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface getCheckout_checkout_lines_totalPrice {
  net: getCheckout_checkout_lines_totalPrice_net;
  gross: getCheckout_checkout_lines_totalPrice_gross;
  currency: string;
}

export interface getCheckout_checkout_lines_variant_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface getCheckout_checkout_lines_variant_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface getCheckout_checkout_lines_variant {
  id: string;
  name: string;
  price: getCheckout_checkout_lines_variant_price | null;
  product: getCheckout_checkout_lines_variant_product;
}

export interface getCheckout_checkout_lines {
  id: string;
  quantity: number;
  totalPrice: getCheckout_checkout_lines_totalPrice | null;
  variant: getCheckout_checkout_lines_variant;
}

export interface getCheckout_checkout {
  token: any;
  id: string;
  totalPrice: getCheckout_checkout_totalPrice | null;
  subtotalPrice: getCheckout_checkout_subtotalPrice | null;
  billingAddress: getCheckout_checkout_billingAddress | null;
  shippingAddress: getCheckout_checkout_shippingAddress | null;
  email: string;
  availableShippingMethods:
    | (getCheckout_checkout_availableShippingMethods | null)[]
    | null;
  shippingMethod: getCheckout_checkout_shippingMethod | null;
  shippingPrice: getCheckout_checkout_shippingPrice | null;
  lines: (getCheckout_checkout_lines | null)[] | null;
}

export interface getCheckout {
  checkout: getCheckout_checkout | null;
}

export interface getCheckoutVariables {
  token: any;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: updateCheckoutLine
// ====================================================

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_totalPrice_net {
  amount: number;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_totalPrice {
  net: updateCheckoutLine_checkoutLinesUpdate_checkout_totalPrice_net;
  gross: updateCheckoutLine_checkoutLinesUpdate_checkout_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice_net {
  amount: number;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice {
  net: updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice_net;
  gross: updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice_gross;
  currency: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_billingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_billingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutLine_checkoutLinesUpdate_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_shippingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_shippingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutLine_checkoutLinesUpdate_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_availableShippingMethods_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_availableShippingMethods {
  id: string;
  name: string;
  price: updateCheckoutLine_checkoutLinesUpdate_checkout_availableShippingMethods_price | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_shippingMethod_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_shippingMethod {
  id: string;
  name: string;
  price: updateCheckoutLine_checkoutLinesUpdate_checkout_shippingMethod_price | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_shippingPrice_net {
  amount: number;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_shippingPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_shippingPrice {
  net: updateCheckoutLine_checkoutLinesUpdate_checkout_shippingPrice_net;
  gross: updateCheckoutLine_checkoutLinesUpdate_checkout_shippingPrice_gross;
  currency: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice_net {
  amount: number;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice {
  net: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice_net;
  gross: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant {
  id: string;
  name: string;
  price: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_price | null;
  product: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines {
  id: string;
  quantity: number;
  totalPrice: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice | null;
  variant: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout {
  token: any;
  id: string;
  totalPrice: updateCheckoutLine_checkoutLinesUpdate_checkout_totalPrice | null;
  subtotalPrice: updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice | null;
  billingAddress: updateCheckoutLine_checkoutLinesUpdate_checkout_billingAddress | null;
  shippingAddress: updateCheckoutLine_checkoutLinesUpdate_checkout_shippingAddress | null;
  email: string;
  availableShippingMethods:
    | (updateCheckoutLine_checkoutLinesUpdate_checkout_availableShippingMethods | null)[]
    | null;
  shippingMethod: updateCheckoutLine_checkoutLinesUpdate_checkout_shippingMethod | null;
  shippingPrice: updateCheckoutLine_checkoutLinesUpdate_checkout_shippingPrice | null;
  lines:
    | (updateCheckoutLine_checkoutLinesUpdate_checkout_lines | null)[]
    | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_errors {
  field: string | null;
  message: string | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate {
  checkout: updateCheckoutLine_checkoutLinesUpdate_checkout | null;
  errors: (updateCheckoutLine_checkoutLinesUpdate_errors | null)[] | null;
}

export interface updateCheckoutLine {
  checkoutLinesUpdate: updateCheckoutLine_checkoutLinesUpdate | null;
}

export interface updateCheckoutLineVariables {
  checkoutId: string;
  lines: (CheckoutLineInput | null)[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: updateCheckoutBillingAddress
// ====================================================

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_errors {
  field: string | null;
  message: string | null;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_totalPrice_net {
  amount: number;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_totalPrice {
  net: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_totalPrice_net;
  gross: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_subtotalPrice_net {
  amount: number;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_subtotalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_subtotalPrice {
  net: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_subtotalPrice_net;
  gross: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_subtotalPrice_gross;
  currency: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_billingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_billingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_availableShippingMethods_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_availableShippingMethods {
  id: string;
  name: string;
  price: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_availableShippingMethods_price | null;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingMethod_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingMethod {
  id: string;
  name: string;
  price: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingMethod_price | null;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingPrice_net {
  amount: number;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingPrice {
  net: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingPrice_net;
  gross: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingPrice_gross;
  currency: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_totalPrice_net {
  amount: number;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_totalPrice {
  net: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_totalPrice_net;
  gross: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_variant_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_variant_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_variant {
  id: string;
  name: string;
  price: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_variant_price | null;
  product: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_variant_product;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines {
  id: string;
  quantity: number;
  totalPrice: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_totalPrice | null;
  variant: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines_variant;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout {
  token: any;
  id: string;
  totalPrice: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_totalPrice | null;
  subtotalPrice: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_subtotalPrice | null;
  billingAddress: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_billingAddress | null;
  shippingAddress: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingAddress | null;
  email: string;
  availableShippingMethods:
    | (updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_availableShippingMethods | null)[]
    | null;
  shippingMethod: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingMethod | null;
  shippingPrice: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_shippingPrice | null;
  lines:
    | (updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout_lines | null)[]
    | null;
}

export interface updateCheckoutBillingAddress_checkoutBillingAddressUpdate {
  errors:
    | (updateCheckoutBillingAddress_checkoutBillingAddressUpdate_errors | null)[]
    | null;
  checkout: updateCheckoutBillingAddress_checkoutBillingAddressUpdate_checkout | null;
}

export interface updateCheckoutBillingAddress {
  checkoutBillingAddressUpdate: updateCheckoutBillingAddress_checkoutBillingAddressUpdate | null;
}

export interface updateCheckoutBillingAddressVariables {
  checkoutId: string;
  billingAddress: AddressInput;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: getPaymentToken
// ====================================================

export interface getPaymentToken {
  paymentClientToken: string | null;
}

export interface getPaymentTokenVariables {
  gateway: GatewaysEnum;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: createPayment
// ====================================================

export interface createPayment_checkoutPaymentCreate_errors {
  field: string | null;
  message: string | null;
}

export interface createPayment_checkoutPaymentCreate {
  errors: (createPayment_checkoutPaymentCreate_errors | null)[] | null;
}

export interface createPayment {
  checkoutPaymentCreate: createPayment_checkoutPaymentCreate | null;
}

export interface createPaymentVariables {
  input: PaymentInput;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: completeCheckout
// ====================================================

export interface completeCheckout_checkoutComplete_errors {
  field: string | null;
  message: string | null;
}

export interface completeCheckout_checkoutComplete_order {
  id: string;
}

export interface completeCheckout_checkoutComplete {
  errors: (completeCheckout_checkoutComplete_errors | null)[] | null;
  order: completeCheckout_checkoutComplete_order | null;
}

export interface completeCheckout {
  checkoutComplete: completeCheckout_checkoutComplete | null;
}

export interface completeCheckoutVariables {
  checkoutId: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: updateCheckoutShippingAddress
// ====================================================

export interface updateCheckoutShippingAddress_checkoutShippingAddressUpdate_errors {
  field: string | null;
  message: string | null;
}

export interface updateCheckoutShippingAddress_checkoutShippingAddressUpdate {
  errors:
    | (updateCheckoutShippingAddress_checkoutShippingAddressUpdate_errors | null)[]
    | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_errors {
  field: string | null;
  message: string | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_totalPrice_net {
  amount: number;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_totalPrice {
  net: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_totalPrice_net;
  gross: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_subtotalPrice_net {
  amount: number;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_subtotalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_subtotalPrice {
  net: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_subtotalPrice_net;
  gross: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_subtotalPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_billingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_billingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_availableShippingMethods_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_availableShippingMethods {
  id: string;
  name: string;
  price: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_availableShippingMethods_price | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingMethod_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingMethod {
  id: string;
  name: string;
  price: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingMethod_price | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingPrice_net {
  amount: number;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingPrice {
  net: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingPrice_net;
  gross: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_totalPrice_net {
  amount: number;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_totalPrice {
  net: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_totalPrice_net;
  gross: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_variant_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_variant_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_variant {
  id: string;
  name: string;
  price: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_variant_price | null;
  product: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_variant_product;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines {
  id: string;
  quantity: number;
  totalPrice: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_totalPrice | null;
  variant: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines_variant;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate_checkout {
  token: any;
  id: string;
  totalPrice: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_totalPrice | null;
  subtotalPrice: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_subtotalPrice | null;
  billingAddress: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_billingAddress | null;
  shippingAddress: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingAddress | null;
  email: string;
  availableShippingMethods:
    | (updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_availableShippingMethods | null)[]
    | null;
  shippingMethod: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingMethod | null;
  shippingPrice: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_shippingPrice | null;
  lines:
    | (updateCheckoutShippingAddress_checkoutEmailUpdate_checkout_lines | null)[]
    | null;
}

export interface updateCheckoutShippingAddress_checkoutEmailUpdate {
  errors:
    | (updateCheckoutShippingAddress_checkoutEmailUpdate_errors | null)[]
    | null;
  checkout: updateCheckoutShippingAddress_checkoutEmailUpdate_checkout | null;
}

export interface updateCheckoutShippingAddress {
  checkoutShippingAddressUpdate: updateCheckoutShippingAddress_checkoutShippingAddressUpdate | null;
  checkoutEmailUpdate: updateCheckoutShippingAddress_checkoutEmailUpdate | null;
}

export interface updateCheckoutShippingAddressVariables {
  checkoutId: string;
  shippingAddress: AddressInput;
  email: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: updateCheckoutShippingOptions
// ====================================================

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_errors {
  field: string | null;
  message: string | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice_net {
  amount: number;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice {
  net: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice_net;
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice_net {
  amount: number;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice {
  net: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice_net;
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress_country {
  code: string;
  country: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods {
  id: string;
  name: string;
  price: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods_price | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod {
  id: string;
  name: string;
  price: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod_price | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice_net {
  amount: number;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice {
  net: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice_net;
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice_net {
  amount: number;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice {
  net: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice_net;
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice_gross;
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant {
  id: string;
  name: string;
  price: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_price | null;
  product: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines {
  id: string;
  quantity: number;
  totalPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice | null;
  variant: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout {
  token: any;
  id: string;
  totalPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice | null;
  subtotalPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice | null;
  billingAddress: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress | null;
  shippingAddress: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress | null;
  email: string;
  availableShippingMethods:
    | (updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods | null)[]
    | null;
  shippingMethod: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod | null;
  shippingPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice | null;
  lines:
    | (updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines | null)[]
    | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate {
  errors:
    | (updateCheckoutShippingOptions_checkoutShippingMethodUpdate_errors | null)[]
    | null;
  checkout: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout | null;
}

export interface updateCheckoutShippingOptions {
  checkoutShippingMethodUpdate: updateCheckoutShippingOptions_checkoutShippingMethodUpdate | null;
}

export interface updateCheckoutShippingOptionsVariables {
  checkoutId: string;
  shippingMethodId: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: Collections
// ====================================================

export interface Collections_collections_edges_node {
  id: string;
  name: string;
}

export interface Collections_collections_edges {
  node: Collections_collections_edges_node;
}

export interface Collections_collections {
  edges: Collections_collections_edges[];
}

export interface Collections {
  collections: Collections_collections | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: createCheckout
// ====================================================

export interface createCheckout_checkoutCreate_errors {
  field: string | null;
  message: string | null;
}

export interface createCheckout_checkoutCreate_checkout_totalPrice_net {
  amount: number;
}

export interface createCheckout_checkoutCreate_checkout_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface createCheckout_checkoutCreate_checkout_totalPrice {
  net: createCheckout_checkoutCreate_checkout_totalPrice_net;
  gross: createCheckout_checkoutCreate_checkout_totalPrice_gross;
  currency: string;
}

export interface createCheckout_checkoutCreate_checkout_subtotalPrice_net {
  amount: number;
}

export interface createCheckout_checkoutCreate_checkout_subtotalPrice_gross {
  amount: number;
  localized: string;
}

export interface createCheckout_checkoutCreate_checkout_subtotalPrice {
  net: createCheckout_checkoutCreate_checkout_subtotalPrice_net;
  gross: createCheckout_checkoutCreate_checkout_subtotalPrice_gross;
  currency: string;
}

export interface createCheckout_checkoutCreate_checkout_billingAddress_country {
  code: string;
  country: string;
}

export interface createCheckout_checkoutCreate_checkout_billingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: createCheckout_checkoutCreate_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface createCheckout_checkoutCreate_checkout_shippingAddress_country {
  code: string;
  country: string;
}

export interface createCheckout_checkoutCreate_checkout_shippingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: createCheckout_checkoutCreate_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface createCheckout_checkoutCreate_checkout_availableShippingMethods_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface createCheckout_checkoutCreate_checkout_availableShippingMethods {
  id: string;
  name: string;
  price: createCheckout_checkoutCreate_checkout_availableShippingMethods_price | null;
}

export interface createCheckout_checkoutCreate_checkout_shippingMethod_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface createCheckout_checkoutCreate_checkout_shippingMethod {
  id: string;
  name: string;
  price: createCheckout_checkoutCreate_checkout_shippingMethod_price | null;
}

export interface createCheckout_checkoutCreate_checkout_shippingPrice_net {
  amount: number;
}

export interface createCheckout_checkoutCreate_checkout_shippingPrice_gross {
  amount: number;
  localized: string;
}

export interface createCheckout_checkoutCreate_checkout_shippingPrice {
  net: createCheckout_checkoutCreate_checkout_shippingPrice_net;
  gross: createCheckout_checkoutCreate_checkout_shippingPrice_gross;
  currency: string;
}

export interface createCheckout_checkoutCreate_checkout_lines_totalPrice_net {
  amount: number;
}

export interface createCheckout_checkoutCreate_checkout_lines_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface createCheckout_checkoutCreate_checkout_lines_totalPrice {
  net: createCheckout_checkoutCreate_checkout_lines_totalPrice_net;
  gross: createCheckout_checkoutCreate_checkout_lines_totalPrice_gross;
  currency: string;
}

export interface createCheckout_checkoutCreate_checkout_lines_variant_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface createCheckout_checkoutCreate_checkout_lines_variant_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface createCheckout_checkoutCreate_checkout_lines_variant {
  id: string;
  name: string;
  price: createCheckout_checkoutCreate_checkout_lines_variant_price | null;
  product: createCheckout_checkoutCreate_checkout_lines_variant_product;
}

export interface createCheckout_checkoutCreate_checkout_lines {
  id: string;
  quantity: number;
  totalPrice: createCheckout_checkoutCreate_checkout_lines_totalPrice | null;
  variant: createCheckout_checkoutCreate_checkout_lines_variant;
}

export interface createCheckout_checkoutCreate_checkout {
  token: any;
  id: string;
  totalPrice: createCheckout_checkoutCreate_checkout_totalPrice | null;
  subtotalPrice: createCheckout_checkoutCreate_checkout_subtotalPrice | null;
  billingAddress: createCheckout_checkoutCreate_checkout_billingAddress | null;
  shippingAddress: createCheckout_checkoutCreate_checkout_shippingAddress | null;
  email: string;
  availableShippingMethods:
    | (createCheckout_checkoutCreate_checkout_availableShippingMethods | null)[]
    | null;
  shippingMethod: createCheckout_checkoutCreate_checkout_shippingMethod | null;
  shippingPrice: createCheckout_checkoutCreate_checkout_shippingPrice | null;
  lines: (createCheckout_checkoutCreate_checkout_lines | null)[] | null;
}

export interface createCheckout_checkoutCreate {
  errors: (createCheckout_checkoutCreate_errors | null)[] | null;
  checkout: createCheckout_checkoutCreate_checkout | null;
}

export interface createCheckout {
  checkoutCreate: createCheckout_checkoutCreate | null;
}

export interface createCheckoutVariables {
  checkoutInput: CheckoutCreateInput;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductsList
// ====================================================

export interface ProductsList_shop_homepageCollection_backgroundImage {
  url: string;
}

export interface ProductsList_shop_homepageCollection_products_edges_node_category {
  id: string;
  name: string;
}

export interface ProductsList_shop_homepageCollection_products_edges_node_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface ProductsList_shop_homepageCollection_products_edges_node {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
  category: ProductsList_shop_homepageCollection_products_edges_node_category;
  price: ProductsList_shop_homepageCollection_products_edges_node_price | null;
}

export interface ProductsList_shop_homepageCollection_products_edges {
  node: ProductsList_shop_homepageCollection_products_edges_node;
}

export interface ProductsList_shop_homepageCollection_products {
  edges: ProductsList_shop_homepageCollection_products_edges[];
}

export interface ProductsList_shop_homepageCollection {
  id: string;
  backgroundImage: ProductsList_shop_homepageCollection_backgroundImage | null;
  name: string;
  products: ProductsList_shop_homepageCollection_products | null;
}

export interface ProductsList_shop {
  homepageCollection: ProductsList_shop_homepageCollection | null;
}

export interface ProductsList_categories_edges_node_backgroundImage {
  url: string;
}

export interface ProductsList_categories_edges_node {
  id: string;
  name: string;
  backgroundImage: ProductsList_categories_edges_node_backgroundImage | null;
}

export interface ProductsList_categories_edges {
  node: ProductsList_categories_edges_node;
}

export interface ProductsList_categories {
  edges: ProductsList_categories_edges[];
}

export interface ProductsList {
  shop: ProductsList_shop | null;
  categories: ProductsList_categories | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: RegisterCutomer
// ====================================================

export interface RegisterCutomer_customerRegister_errors {
  field: string | null;
  message: string | null;
}

export interface RegisterCutomer_customerRegister {
  errors: (RegisterCutomer_customerRegister_errors | null)[] | null;
}

export interface RegisterCutomer {
  customerRegister: RegisterCutomer_customerRegister | null;
}

export interface RegisterCutomerVariables {
  email: string;
  password: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: MainMenu
// ====================================================

export interface MainMenu_shop_navigation_main_items_category {
  id: string;
}

export interface MainMenu_shop_navigation_main_items {
  id: string;
  name: string;
  category: MainMenu_shop_navigation_main_items_category | null;
}

export interface MainMenu_shop_navigation_main {
  id: string;
  items: (MainMenu_shop_navigation_main_items | null)[] | null;
}

export interface MainMenu_shop_navigation {
  main: MainMenu_shop_navigation_main | null;
}

export interface MainMenu_shop {
  navigation: MainMenu_shop_navigation | null;
}

export interface MainMenu {
  shop: MainMenu_shop | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: Categories
// ====================================================

export interface Categories_categories_edges_node {
  id: string;
  name: string;
  url: string | null;
}

export interface Categories_categories_edges {
  node: Categories_categories_edges_node;
}

export interface Categories_categories {
  edges: Categories_categories_edges[];
}

export interface Categories {
  categories: Categories_categories | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductDetails
// ====================================================

export interface ProductDetails_product_category_products_edges_node_category {
  id: string;
  name: string;
}

export interface ProductDetails_product_category_products_edges_node_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface ProductDetails_product_category_products_edges_node {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
  category: ProductDetails_product_category_products_edges_node_category;
  price: ProductDetails_product_category_products_edges_node_price | null;
}

export interface ProductDetails_product_category_products_edges {
  node: ProductDetails_product_category_products_edges_node;
}

export interface ProductDetails_product_category_products {
  edges: ProductDetails_product_category_products_edges[];
}

export interface ProductDetails_product_category {
  id: string;
  name: string;
  products: ProductDetails_product_category_products | null;
}

export interface ProductDetails_product_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface ProductDetails_product_images {
  id: string;
  url: string;
}

export interface ProductDetails_product_variants_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface ProductDetails_product_variants_attributes_attribute {
  id: string;
  name: string | null;
}

export interface ProductDetails_product_variants_attributes_value {
  id: string;
  name: string | null;
  value: string | null;
}

export interface ProductDetails_product_variants_attributes {
  attribute: ProductDetails_product_variants_attributes_attribute;
  value: ProductDetails_product_variants_attributes_value;
}

export interface ProductDetails_product_variants {
  id: string;
  name: string;
  stockQuantity: number;
  price: ProductDetails_product_variants_price | null;
  attributes: ProductDetails_product_variants_attributes[];
}

export interface ProductDetails_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
  description: string;
  category: ProductDetails_product_category;
  price: ProductDetails_product_price | null;
  images: (ProductDetails_product_images | null)[] | null;
  variants: (ProductDetails_product_variants | null)[] | null;
}

export interface ProductDetails {
  product: ProductDetails_product | null;
}

export interface ProductDetailsVariables {
  id: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: VariantList
// ====================================================

export interface VariantList_productVariants_edges_node_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface VariantList_productVariants_edges_node_attributes_attribute {
  id: string;
  name: string | null;
}

export interface VariantList_productVariants_edges_node_attributes_value {
  id: string;
  name: string | null;
  value: string | null;
}

export interface VariantList_productVariants_edges_node_attributes {
  attribute: VariantList_productVariants_edges_node_attributes_attribute;
  value: VariantList_productVariants_edges_node_attributes_value;
}

export interface VariantList_productVariants_edges_node_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface VariantList_productVariants_edges_node {
  id: string;
  name: string;
  stockQuantity: number;
  price: VariantList_productVariants_edges_node_price | null;
  attributes: VariantList_productVariants_edges_node_attributes[];
  product: VariantList_productVariants_edges_node_product;
}

export interface VariantList_productVariants_edges {
  node: VariantList_productVariants_edges_node;
}

export interface VariantList_productVariants {
  edges: VariantList_productVariants_edges[];
}

export interface VariantList {
  productVariants: VariantList_productVariants | null;
}

export interface VariantListVariables {
  ids?: string[] | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchResults
// ====================================================

export interface SearchResults_products_edges_node_category {
  id: string;
  name: string;
}

export interface SearchResults_products_edges_node {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
  url: string;
  category: SearchResults_products_edges_node_category;
}

export interface SearchResults_products_edges {
  node: SearchResults_products_edges_node;
}

export interface SearchResults_products_pageInfo {
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SearchResults_products {
  edges: SearchResults_products_edges[];
  pageInfo: SearchResults_products_pageInfo;
}

export interface SearchResults {
  products: SearchResults_products | null;
}

export interface SearchResultsVariables {
  query: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: getShop
// ====================================================

export interface getShop_shop_defaultCountry {
  code: string;
  country: string;
}

export interface getShop_shop_countries {
  country: string;
  code: string;
}

export interface getShop_shop_geolocalization_country {
  code: string;
  country: string;
}

export interface getShop_shop_geolocalization {
  country: getShop_shop_geolocalization_country | null;
}

export interface getShop_shop {
  defaultCountry: getShop_shop_defaultCountry | null;
  countries: (getShop_shop_countries | null)[];
  geolocalization: getShop_shop_geolocalization | null;
}

export interface getShop {
  shop: getShop_shop | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: TokenAuth
// ====================================================

export interface TokenAuth_tokenCreate_errors {
  field: string | null;
  message: string | null;
}

export interface TokenAuth_tokenCreate_user {
  id: string;
  email: string;
  isStaff: boolean;
  note: string | null;
}

export interface TokenAuth_tokenCreate {
  token: string | null;
  errors: (TokenAuth_tokenCreate_errors | null)[] | null;
  user: TokenAuth_tokenCreate_user | null;
}

export interface TokenAuth {
  tokenCreate: TokenAuth_tokenCreate | null;
}

export interface TokenAuthVariables {
  email: string;
  password: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VerifyToken
// ====================================================

export interface VerifyToken_tokenVerify_user {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  note: string | null;
}

export interface VerifyToken_tokenVerify {
  payload: any | null;
  user: VerifyToken_tokenVerify_user | null;
}

export interface VerifyToken {
  tokenVerify: VerifyToken_tokenVerify | null;
}

export interface VerifyTokenVariables {
  token: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: Article
// ====================================================

export interface Article_page {
  content: string;
  id: string;
  seoDescription: string | null;
  seoTitle: string | null;
  slug: string;
  title: string;
}

export interface Article_shop_homepageCollection_backgroundImage {
  url: string;
}

export interface Article_shop_homepageCollection {
  id: string;
  backgroundImage: Article_shop_homepageCollection_backgroundImage | null;
}

export interface Article_shop {
  homepageCollection: Article_shop_homepageCollection | null;
}

export interface Article {
  page: Article_page | null;
  shop: Article_shop | null;
}

export interface ArticleVariables {
  slug: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: Category
// ====================================================

export interface Category_products_edges_node_category {
  id: string;
  name: string;
}

export interface Category_products_edges_node_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface Category_products_edges_node {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
  category: Category_products_edges_node_category;
  price: Category_products_edges_node_price | null;
}

export interface Category_products_edges {
  node: Category_products_edges_node;
}

export interface Category_products_pageInfo {
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface Category_products {
  totalCount: number | null;
  edges: Category_products_edges[];
  pageInfo: Category_products_pageInfo;
}

export interface Category_category_backgroundImage {
  url: string;
}

export interface Category_category_ancestors_edges_node {
  id: string;
  name: string;
}

export interface Category_category_ancestors_edges {
  node: Category_category_ancestors_edges_node;
}

export interface Category_category_ancestors {
  edges: Category_category_ancestors_edges[];
}

export interface Category_category {
  id: string;
  name: string;
  backgroundImage: Category_category_backgroundImage | null;
  ancestors: Category_category_ancestors | null;
}

export interface Category_attributes_edges_node_values {
  id: string;
  name: string | null;
  slug: string | null;
}

export interface Category_attributes_edges_node {
  id: string;
  name: string | null;
  slug: string | null;
  values: (Category_attributes_edges_node_values | null)[] | null;
}

export interface Category_attributes_edges {
  node: Category_attributes_edges_node;
}

export interface Category_attributes {
  edges: Category_attributes_edges[];
}

export interface Category {
  products: Category_products | null;
  category: Category_category | null;
  attributes: Category_attributes | null;
}

export interface CategoryVariables {
  id: string;
  attributes?: (any | null)[] | null;
  after?: string | null;
  pageSize?: number | null;
  sortBy?: ProductOrder | null;
  priceLte?: number | null;
  priceGte?: number | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchProducts
// ====================================================

export interface SearchProducts_products_edges_node_category {
  id: string;
  name: string;
}

export interface SearchProducts_products_edges_node_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface SearchProducts_products_edges_node {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
  category: SearchProducts_products_edges_node_category;
  price: SearchProducts_products_edges_node_price | null;
}

export interface SearchProducts_products_edges {
  node: SearchProducts_products_edges_node;
}

export interface SearchProducts_products_pageInfo {
  endCursor: string | null;
  hasNextPage: boolean;
}

export interface SearchProducts_products {
  totalCount: number | null;
  edges: SearchProducts_products_edges[];
  pageInfo: SearchProducts_products_pageInfo;
}

export interface SearchProducts_attributes_edges_node_values {
  id: string;
  name: string | null;
  slug: string | null;
}

export interface SearchProducts_attributes_edges_node {
  id: string;
  name: string | null;
  slug: string | null;
  values: (SearchProducts_attributes_edges_node_values | null)[] | null;
}

export interface SearchProducts_attributes_edges {
  node: SearchProducts_attributes_edges_node;
}

export interface SearchProducts_attributes {
  edges: SearchProducts_attributes_edges[];
}

export interface SearchProducts {
  products: SearchProducts_products | null;
  attributes: SearchProducts_attributes | null;
}

export interface SearchProductsVariables {
  query: string;
  attributes?: (any | null)[] | null;
  pageSize?: number | null;
  sortBy?: ProductOrder | null;
  after?: string | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: Checkout
// ====================================================

export interface Checkout_totalPrice_net {
  amount: number;
}

export interface Checkout_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface Checkout_totalPrice {
  net: Checkout_totalPrice_net;
  gross: Checkout_totalPrice_gross;
  currency: string;
}

export interface Checkout_subtotalPrice_net {
  amount: number;
}

export interface Checkout_subtotalPrice_gross {
  amount: number;
  localized: string;
}

export interface Checkout_subtotalPrice {
  net: Checkout_subtotalPrice_net;
  gross: Checkout_subtotalPrice_gross;
  currency: string;
}

export interface Checkout_billingAddress_country {
  code: string;
  country: string;
}

export interface Checkout_billingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: Checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface Checkout_shippingAddress_country {
  code: string;
  country: string;
}

export interface Checkout_shippingAddress {
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  country: Checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface Checkout_availableShippingMethods_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface Checkout_availableShippingMethods {
  id: string;
  name: string;
  price: Checkout_availableShippingMethods_price | null;
}

export interface Checkout_shippingMethod_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface Checkout_shippingMethod {
  id: string;
  name: string;
  price: Checkout_shippingMethod_price | null;
}

export interface Checkout_shippingPrice_net {
  amount: number;
}

export interface Checkout_shippingPrice_gross {
  amount: number;
  localized: string;
}

export interface Checkout_shippingPrice {
  net: Checkout_shippingPrice_net;
  gross: Checkout_shippingPrice_gross;
  currency: string;
}

export interface Checkout_lines_totalPrice_net {
  amount: number;
}

export interface Checkout_lines_totalPrice_gross {
  amount: number;
  localized: string;
}

export interface Checkout_lines_totalPrice {
  net: Checkout_lines_totalPrice_net;
  gross: Checkout_lines_totalPrice_gross;
  currency: string;
}

export interface Checkout_lines_variant_price {
  amount: number;
  currency: string;
  localized: string;
}

export interface Checkout_lines_variant_product {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

export interface Checkout_lines_variant {
  id: string;
  name: string;
  price: Checkout_lines_variant_price | null;
  product: Checkout_lines_variant_product;
}

export interface Checkout_lines {
  id: string;
  quantity: number;
  totalPrice: Checkout_lines_totalPrice | null;
  variant: Checkout_lines_variant;
}

export interface Checkout {
  token: any;
  id: string;
  totalPrice: Checkout_totalPrice | null;
  subtotalPrice: Checkout_subtotalPrice | null;
  billingAddress: Checkout_billingAddress | null;
  shippingAddress: Checkout_shippingAddress | null;
  email: string;
  availableShippingMethods: (Checkout_availableShippingMethods | null)[] | null;
  shippingMethod: Checkout_shippingMethod | null;
  shippingPrice: Checkout_shippingPrice | null;
  lines: (Checkout_lines | null)[] | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: BasicProductFields
// ====================================================

export interface BasicProductFields {
  id: string;
  name: string;
  thumbnailUrl: string | null;
  thumbnailUrl2x: string | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductVariantFields
// ====================================================

export interface ProductVariantFields_price {
  currency: string;
  amount: number;
  localized: string;
}

export interface ProductVariantFields_attributes_attribute {
  id: string;
  name: string | null;
}

export interface ProductVariantFields_attributes_value {
  id: string;
  name: string | null;
  value: string | null;
}

export interface ProductVariantFields_attributes {
  attribute: ProductVariantFields_attributes_attribute;
  value: ProductVariantFields_attributes_value;
}

export interface ProductVariantFields {
  id: string;
  name: string;
  stockQuantity: number;
  price: ProductVariantFields_price | null;
  attributes: ProductVariantFields_attributes[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: User
// ====================================================

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  note: string | null;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum GatewaysEnum {
  BRAINTREE = "BRAINTREE",
  DUMMY = "DUMMY"
}

export enum ProductOrderField {
  NAME = "NAME",
  PRICE = "PRICE"
}

export enum OrderDirection {
  ASC = "ASC",
  DESC = "DESC"
}

// null
export interface CheckoutLineInput {
  quantity?: number | null;
  variantId?: string | null;
}

// null
export interface AddressInput {
  firstName?: string | null;
  lastName?: string | null;
  companyName?: string | null;
  streetAddress1?: string | null;
  streetAddress2?: string | null;
  city?: string | null;
  cityArea?: string | null;
  postalCode?: string | null;
  country: string;
  countryArea?: string | null;
  phone?: string | null;
}

// null
export interface PaymentInput {
  gateway?: GatewaysEnum | null;
  checkoutId?: string | null;
  token: string;
  amount: any;
  billingAddress?: AddressInput | null;
}

// null
export interface CheckoutCreateInput {
  lines?: (CheckoutLineInput | null)[] | null;
  email?: string | null;
  shippingAddress?: AddressInput | null;
}

// null
export interface ProductOrder {
  field: ProductOrderField;
  direction: OrderDirection;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
