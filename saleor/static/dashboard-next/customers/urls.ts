export const customerSection = "/customers/";
export const customerListUrl = customerSection;
export const customerUrl = (id: string) => customerSection + id + "/";

export const customerAddUrl = customerSection + "add/";
export const customerRemoveUrl = (id: string) => customerUrl(id) + "remove/";
