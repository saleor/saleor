import * as urlJoin from "url-join";

import { AttributeTypeEnum } from "../../../types/globalTypes";
import { productTypePath } from "../../urls";

export const addAttributePath = (
  productTypeId: string,
  type: AttributeTypeEnum
) =>
  type === AttributeTypeEnum.PRODUCT
    ? urlJoin(productTypePath(productTypeId), "attribute/product/add")
    : urlJoin(productTypePath(productTypeId), "attribute/variant/add");
export const addAttributeUrl = (
  productTypeId: string,
  type: AttributeTypeEnum
) => addAttributePath(encodeURIComponent(productTypeId), type);

export const editAttributePath = (productTypeId: string, attributeId: string) =>
  urlJoin(productTypePath(productTypeId), "attribute", attributeId);
export const editAttributeUrl = (productTypeId: string, attributeId: string) =>
  editAttributePath(
    encodeURIComponent(productTypeId),
    encodeURIComponent(attributeId)
  );
export const productTypeRemovePath = (id: string) =>
  urlJoin(productTypePath(id), "remove");
export const productTypeRemoveUrl = (id: string) =>
  productTypeRemovePath(encodeURIComponent(id));
