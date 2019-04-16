import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { Dialog, SingleAction } from "../types";

export const customerSection = "/customers/";

export const customerListPath = customerSection;
export const customerListUrl = customerListPath;

export const customerPath = (id: string) => urlJoin(customerSection, id);
export type CustomerUrlDialog = "remove";
export type CustomerUrlQueryParams = Dialog<CustomerUrlDialog>;
export const customerUrl = (id: string, params?: CustomerUrlQueryParams) =>
  customerPath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const customerAddPath = urlJoin(customerSection, "add");
export const customerAddUrl = customerAddPath;

export const customerAddressesPath = (id: string) =>
  urlJoin(customerPath(id), "addresses");
export type CustomerAddressesUrlDialog = "add" | "edit" | "remove";
export type CustomerAddressesUrlQueryParams = Dialog<
  CustomerAddressesUrlDialog
> &
  SingleAction;
export const customerAddressesUrl = (
  id: string,
  params?: CustomerAddressesUrlQueryParams
) => customerAddressesPath(encodeURIComponent(id)) + "?" + stringifyQs(params);
