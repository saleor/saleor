import { FormChange } from "@saleor/hooks/useForm";
import { FormsetChange } from "@saleor/hooks/useFormset";
import { ProductType } from "./data";

export function createAttributeChangeHandler(
  changeAttributeData: FormsetChange,
  triggerChange: () => void
): FormsetChange {
  return (id: string, value: string) => {
    triggerChange();
    changeAttributeData(id, value);
  };
}

export function createProductTypeSelectHandler(
  productTypeChoiceList: ProductType[],
  setProductType: (productType: ProductType) => void,
  change: FormChange
): FormChange {
  return (event: React.ChangeEvent<any>) => {
    const id = event.target.value;
    const selectedProductType = productTypeChoiceList.find(
      productType => productType.id === id
    );
    setProductType(selectedProductType);
    change(event);
    change({
      target: {
        name: "attributes",
        value: selectedProductType.productAttributes.map(attribute => ({
          slug: attribute.slug,
          value: ""
        }))
      }
    } as any);
  };
}
