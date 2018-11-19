import * as urlJoin from "url-join";
import { productVariantEditUrl } from "../../urls";

export const productVariantRemoveUrl = (productId: string, variantId: string) =>
  urlJoin(productVariantEditUrl(productId, variantId), "remove");
