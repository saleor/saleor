import * as urlJoin from "url-join";
import { productVariantEditPath } from "../../urls";

export const productVariantRemovePath = (
  productId: string,
  variantId: string
) => urlJoin(productVariantEditPath(productId, variantId), "remove");
export const productVariantRemoveUrl = (productId: string, variantId: string) =>
  productVariantRemovePath(
    encodeURIComponent(productId),
    encodeURIComponent(variantId)
  );
