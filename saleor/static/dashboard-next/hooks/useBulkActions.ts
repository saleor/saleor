import { useState } from "react";
import { Node } from "../types";

function useBulkActions(initial: string[] = []) {
  const [listElements, setListElements] = useState(initial);

  function isSelected(id: string) {
    return !!listElements.find(listElement => listElement === id);
  }

  function add(id: string) {
    setListElements([...listElements, id]);
  }

  function remove(id: string) {
    setListElements(listElements.filter(listElement => listElement !== id));
  }

  function reset() {
    setListElements([]);
  }

  function toggle(id: string) {
    isSelected(id) ? remove(id) : add(id);
  }

  function toggleAll(items: Node[], selected: number) {
    const allItems = items.map(item => item.id);
    reset();
    if (selected !== allItems.length) {
      setListElements(allItems);
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
