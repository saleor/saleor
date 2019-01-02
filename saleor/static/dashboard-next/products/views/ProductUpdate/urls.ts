import * as urlJoin from "url-join";
import { productPath } from "../../urls";

export const productRemovePath = (id: string) =>
  urlJoin(productPath(id), "remove");
export const productRemoveUrl = (id: string) =>
  productRemovePath(encodeURIComponent(id));
