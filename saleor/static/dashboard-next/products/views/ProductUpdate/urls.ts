import * as urlJoin from "url-join";
import { productUrl } from "../../urls";

export const productRemoveUrl = (id: string) =>
  urlJoin(productUrl(id), "remove");
