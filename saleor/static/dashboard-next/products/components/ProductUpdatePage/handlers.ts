import { FormChange } from "@saleor/components/Form";
import { SingleAutocompleteChoiceType } from "@saleor/components/SingleAutocompleteSelectField";
import { SearchCategories_categories_edges_node } from "@saleor/containers/SearchCategories/types/SearchCategories";
import { Collection, ProductUpdatePageFormData } from "./data";
import { FormsetChange } from "@saleor/hooks/useFormset";

export function createCollectionSelectHandler(
  data: ProductUpdatePageFormData,
  collections: SingleAutocompleteChoiceType[],
  selectedCollections: Collection[],
  setSelectedCollections: (collections: Collection[]) => void,
  change: FormChange
): FormChange {
  return (event: React.ChangeEvent<any>) => {
    const id = event.target.value;
    const collectionIndex = data.collections.indexOf(id);
    const collectionList =
      collectionIndex === -1
        ? [
            ...selectedCollections,
            {
              id,
              label: collections.find(collection => collection.value === id)
                .label
            }
          ]
        : [
            ...selectedCollections.slice(0, collectionIndex),
            ...selectedCollections.slice(collectionIndex + 1)
          ];

    setSelectedCollections(collectionList);
    change({
      target: {
        name: "collections",
        value: collectionList.map(collection => collection.id)
      }
    } as any);
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
