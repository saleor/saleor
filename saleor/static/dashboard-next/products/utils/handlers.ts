import { FormChange } from "@saleor/components/Form";
import { SearchCategories_categories_edges_node } from "@saleor/containers/SearchCategories/types/SearchCategories";
import { FormsetChange } from "@saleor/hooks/useFormset";
import { ProductType } from "./data";

export function createCollectionSelectHandler(
  change: FormChange,
  triggerChange: () => void
): FormChange {
  return (event: React.ChangeEvent<any>) => {
    change(event);
    triggerChange();
  };
}

export function createCategorySelectHandler(
  categoryChoiceList: SearchCategories_categories_edges_node[],
  setSelectedCategory: (id: string) => void,
  change: FormChange
): FormChange {
  return (event: React.ChangeEvent<any>) => {
    const id = event.target.value;
    setSelectedCategory(
      categoryChoiceList.find(category => category.id === id).name
    );
    change(event);
  };
}

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
