import * as urlJoin from "url-join";

import { productImagePath } from "../../urls";

export const productImageRemovePath = (productId: string, imageId: string) =>
  urlJoin(productImagePath(productId, imageId), "remove");
export const productImageRemoveUrl = (productId: string, imageId: string) =>
  productImageRemovePath(
    encodeURIComponent(productId),
    encodeURIComponent(imageId)
  );
