import { useState } from "react";

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

  function toggleAll(items, selected) {
    const allItems = [];
    items.map(item => {
      allItems.push(item.id);
    });
    if (selected === allItems.length) {
      reset();
    } else {
      reset();
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
