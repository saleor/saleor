import * as urlJoin from "url-join";

const productTypeSection = "/productTypes/";
export const productTypeListUrl = productTypeSection;
export const productTypeAddUrl = urlJoin(productTypeSection, "add");
export const productTypeUrl = (id: string) => urlJoin(productTypeSection, id);
