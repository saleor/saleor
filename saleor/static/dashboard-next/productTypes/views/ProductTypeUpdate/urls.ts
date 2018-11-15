import { AttributeTypeEnum } from "../../../types/globalTypes";
import { productTypeDetailsUrl } from "../../urls";

export const addAttributeUrl = (
  productTypeId: string,
  type: AttributeTypeEnum
) =>
  type === AttributeTypeEnum.PRODUCT
    ? productTypeDetailsUrl(productTypeId) + "attribute/product/add"
    : productTypeDetailsUrl(productTypeId) + "attribute/variant/add";
export const editAttributeUrl = (productTypeId: string, attributeId: string) =>
  productTypeDetailsUrl(productTypeId) + "attribute/" + attributeId;
