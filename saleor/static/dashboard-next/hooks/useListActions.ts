import { useEffect, useState } from "react";

function useListActions<TData>(
  initial: TData[] = [],
  compareFunc: (a: TData, b: TData) => boolean = (a, b) => a === b
) {
  const [listElements, setListElements] = useState(initial);

  useEffect(() => setListElements(initial), [JSON.stringify(initial)]);

  function isSelected(data: TData) {
    return !!listElements.find(listElement => compareFunc(listElement, data));
  }

  function add(data: TData) {
    setListElements([...listElements, data]);
  }

  function remove(data: TData) {
    setListElements(
      listElements.filter(listElement => !compareFunc(listElement, data))
    );
  }

  function reset() {
    setListElements([]);
  }

  function toggle(data: TData) {
    isSelected(data) ? remove(data) : add(data);
  }

  function set(data: TData[]) {
    setListElements(data);
  }

  return {
    add,
    isSelected,
    listElements,
    remove,
    reset,
    set,
    toggle
  };
}
export default useListActions;
