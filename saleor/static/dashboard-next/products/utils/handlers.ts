import { FormChange } from "@saleor/hooks/useForm";
import { FormsetChange, FormsetData } from "@saleor/hooks/useFormset";
import { maybe } from "@saleor/misc";
import { toggle } from "@saleor/utils/lists";
import { ProductAttributeInputData } from "../components/ProductAttributes";
import {
  getAttributeInputFromProductType,
  ProductAttributeValueChoices,
  ProductType
} from "./data";

export function createAttributeChangeHandler(
  changeAttributeData: FormsetChange<string[]>,
  setSelectedAttributes: (data: ProductAttributeValueChoices[]) => void,
  selectedAttributes: ProductAttributeValueChoices[],
  attributes: FormsetData<ProductAttributeInputData>,
  triggerChange: () => void
): FormsetChange {
  return (attributeId: string, value: string) => {
    const attributeValue = attributes
      .find(attribute => attribute.id === attributeId)
      .data.values.find(attributeValue => attributeValue.slug === value);

    const valueChoice = {
      label: maybe(() => attributeValue.name, value),
      value
    };

    const itemIndex = selectedAttributes.findIndex(
      item => item.id === attributeId
    );
    const attribute = selectedAttributes[itemIndex];

    setSelectedAttributes([
      ...selectedAttributes.slice(0, itemIndex),
      {
        ...attribute,
        values: [valueChoice]
      },
      ...selectedAttributes.slice(itemIndex + 1)
    ]);

    triggerChange();
    changeAttributeData(attributeId, [value]);
  };
}

export function createAttributeMultiChangeHandler(
  changeAttributeData: FormsetChange<string[]>,
  setSelectedAttributes: (data: ProductAttributeValueChoices[]) => void,
  selectedAttributes: ProductAttributeValueChoices[],
  attributes: FormsetData<ProductAttributeInputData>,
  triggerChange: () => void
): FormsetChange {
  return (attributeId: string, value: string) => {
    const attributeValue = attributes
      .find(attribute => attribute.id === attributeId)
      .data.values.find(attributeValue => attributeValue.slug === value);

    const valueChoice = {
      label: attributeValue ? attributeValue.name : value,
      value
    };

    const itemIndex = selectedAttributes.findIndex(
      item => item.id === attributeId
    );
    const attributeValues = selectedAttributes[itemIndex].values;

    const newAttributeValues = toggle(
      valueChoice,
      attributeValues,
      (a, b) => a.value === b.value
    );

    const newSelectedAttributes = [
      ...selectedAttributes.slice(0, itemIndex),
      {
        ...selectedAttributes[itemIndex],
        values: newAttributeValues
      },
      ...selectedAttributes.slice(itemIndex + 1)
    ];
    setSelectedAttributes(newSelectedAttributes);

    triggerChange();
    changeAttributeData(
      attributeId,
      newAttributeValues.map(({ value }) => value)
    );
  };
}

export function createProductTypeSelectHandler(
  change: FormChange,
  setAttributes: (data: FormsetData<ProductAttributeInputData>) => void,
  setSelectedAttributes: (data: ProductAttributeValueChoices[]) => void,
  setProductType: (productType: ProductType) => void,
  productTypeChoiceList: ProductType[]
): FormChange {
  return (event: React.ChangeEvent<any>) => {
    const id = event.target.value;
    const selectedProductType = productTypeChoiceList.find(
      productType => productType.id === id
    );
    setProductType(selectedProductType);
    change(event);

    setAttributes(getAttributeInputFromProductType(selectedProductType));
    setSelectedAttributes(
      selectedProductType.productAttributes.map(attribute => ({
        id: attribute.id,
        values: []
      }))
    );
  };
}
