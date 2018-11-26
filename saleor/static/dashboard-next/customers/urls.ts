import * as urlJoin from "url-join";

export const customerSection = "/customers/";
export const customerListUrl = customerSection;
export const customerUrl = (id: string) => urlJoin(customerSection, id);

export const customerAddUrl = urlJoin(customerSection, "add");
export const customerRemoveUrl = (id: string) =>
  urlJoin(customerUrl(id), "remove");
