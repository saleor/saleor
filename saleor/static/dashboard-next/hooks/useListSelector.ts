import { useState } from "react";

function useListSelector(initial: string[] = []) {
  const [listElements, setListElements] = useState(initial);

  function isMember(id: string) {
    return !!listElements.find(listElement => listElement === id);
  }

  function add(id: string) {
    setListElements([...listElements, id]);
  }

  function remove(id: string) {
    setListElements(listElements.filter(listElement => listElement !== id));
  }

  function reset() {
    setListElements(initial);
  }

  function toggle(id: string) {
    isMember(id) ? remove(id) : add(id);
  }

  return {
    add,
    isMember,
    listElements,
    remove,
    reset,
    toggle
  };
}
export default useListSelector;
