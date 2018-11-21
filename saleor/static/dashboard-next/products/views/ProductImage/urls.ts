import * as urlJoin from "url-join";

import { productImageUrl } from "../../urls";

export const productImageRemoveUrl = (productId: string, imageId: string) =>
  urlJoin(productImageUrl(productId, imageId), "remove");
