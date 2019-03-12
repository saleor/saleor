import * as urlJoin from "url-join";

export const customerSection = "/customers/";

export const customerListPath = customerSection;
export const customerListUrl = customerListPath;

export const customerPath = (id: string) => urlJoin(customerSection, id);
export const customerUrl = (id: string) => customerPath(encodeURIComponent(id));

export const customerAddPath = urlJoin(customerSection, "add");
export const customerAddUrl = customerAddPath;

export const customerRemovePath = (id: string) =>
  urlJoin(customerPath(id), "remove");
export const customerRemoveUrl = (id: string) =>
  customerRemovePath(encodeURIComponent(id));

export const customerAddressesPath = (id: string) =>
  urlJoin(customerPath(id), "addresses");
export const customerAddressesUrl = (id: string) =>
  customerAddressesPath(encodeURIComponent(id));
