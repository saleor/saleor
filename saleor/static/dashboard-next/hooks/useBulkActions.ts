import { Node } from "../types";
import useListActions from "./useListActions";

function useBulkActions(initial: string[] = []) {
  const {
    add,
    isSelected,
    listElements,
    remove,
    reset,
    set,
    toggle
  } = useListActions<string>(initial);

  function toggleAll(items: Node[], selected: number) {
    const allItems = items.map(item => item.id);
    reset();
    if (selected !== allItems.length) {
      set(allItems);
    }
  }

  return {
    add,
    isSelected,
    listElements,
    remove,
    reset,
    toggle,
    toggleAll
  };
}
export default useBulkActions;
