import * as urlJoin from "url-join";

import { AttributeTypeEnum } from "../../../types/globalTypes";
import { productTypeUrl } from "../../urls";

export const addAttributeUrl = (
  productTypeId: string,
  type: AttributeTypeEnum
) =>
  type === AttributeTypeEnum.PRODUCT
    ? urlJoin(productTypeUrl(productTypeId), "attribute/product/add")
    : urlJoin(productTypeUrl(productTypeId), "attribute/variant/add");
export const editAttributeUrl = (productTypeId: string, attributeId: string) =>
  urlJoin(productTypeUrl(productTypeId), "attribute", attributeId);
