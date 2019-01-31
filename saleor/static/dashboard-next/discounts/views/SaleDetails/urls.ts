import * as urlJoin from "url-join";
import { salePath } from "../../urls";

export const saleAssignProductsPath = (id: string) =>
  urlJoin(salePath(id), "assign-product");
export const saleAssignProductsUrl = (id: string) =>
  saleAssignProductsPath(encodeURIComponent(id));
