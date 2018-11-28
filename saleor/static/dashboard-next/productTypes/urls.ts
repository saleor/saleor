import * as urlJoin from "url-join";

const productTypeSection = "/productTypes/";

export const productTypeListPath = productTypeSection;
export const productTypeListUrl = productTypeListPath;

export const productTypeAddPath = urlJoin(productTypeSection, "add");
export const productTypeAddUrl = productTypeAddPath;

export const productTypePath = (id: string) => urlJoin(productTypeSection, id);
export const productTypeUrl = (id: string) =>
  productTypePath(encodeURIComponent(id));
