import { FormChange } from "@saleor/hooks/useForm";
import { FormsetChange, FormsetData } from "@saleor/hooks/useFormset";
import { toggle } from "@saleor/utils/lists";
import { ProductAttributeInputData } from "../components/ProductAttributes";
import {
  getAttributeInputFromProductType,
  ProductAttributeValueChoices,
  ProductType
} from "./data";

export function createAttributeChangeHandler(
  changeAttributeData: FormsetChange<string>,
  setSelectedAttributes: (data: ProductAttributeValueChoices[]) => void,
  selectedAttributes: ProductAttributeValueChoices[],
  triggerChange: () => void
): FormsetChange {
  return (id: string, value: string) => {
    const itemIndex = selectedAttributes.findIndex(item => item.id === id);
    const attribute = selectedAttributes[itemIndex];

    setSelectedAttributes([
      ...selectedAttributes.slice(0, itemIndex),
      {
        ...attribute,
        values: [
          attribute.values.find(
            attributeValue => attributeValue.value === value
          )
        ]
      },
      ...selectedAttributes.slice(itemIndex + 1)
    ]);

    triggerChange();
    changeAttributeData(id, value);
  };
}

export function createAttributeMultiChangeHandler(
  changeAttributeData: FormsetChange<string[]>,
  setSelectedAttributes: (data: ProductAttributeValueChoices[]) => void,
  selectedAttributes: ProductAttributeValueChoices[],
  attributes: FormsetData<ProductAttributeInputData>,
  triggerChange: () => void
): FormsetChange {
  return (id: string, value: string) => {
    const attributeValue = attributes
      .find(attribute => attribute.id === id)
      .data.values.find(attributeValue => attributeValue.id === value);

    const valueChoice = {
      label: attributeValue.name,
      value
    };

    const itemIndex = selectedAttributes.findIndex(item => item.id === id);
    const field = selectedAttributes[itemIndex].values;

    const attributeValues = toggle(
      valueChoice,
      field,
      (a, b) => a.value === b.value
    );

    const newSelectedAttributes = [
      ...selectedAttributes.slice(0, itemIndex),
      {
        ...selectedAttributes[itemIndex],
        values: attributeValues
      },
      ...selectedAttributes.slice(itemIndex + 1)
    ];
    setSelectedAttributes(newSelectedAttributes);

    triggerChange();
    changeAttributeData(id, attributeValues.map(({ value }) => value));
  };
}

export function createProductTypeSelectHandler(
  productTypeChoiceList: ProductType[],
  setProductType: (productType: ProductType) => void,
  change: FormChange,
  set: (data: FormsetData<ProductAttributeInputData>) => void
): FormChange {
  return (event: React.ChangeEvent<any>) => {
    const id = event.target.value;
    const selectedProductType = productTypeChoiceList.find(
      productType => productType.id === id
    );
    setProductType(selectedProductType);
    change(event);

    set(getAttributeInputFromProductType(selectedProductType));
  };
}
