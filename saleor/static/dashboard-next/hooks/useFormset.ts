import isEqual from "lodash-es/isEqual";

import { toggle } from "@saleor/utils/lists";
import useStateFromProps from "./useStateFromProps";

export type FormsetChange = (id: string, value: any) => void;
export interface FormsetAtomicData<TData = object> {
  data: TData;
  id: string;
  label: string;
  value: any;
}
export type FormsetData<TData = object> = Array<FormsetAtomicData<TData>>;
export interface UseFormsetOutput<TData = object> {
  change: FormsetChange;
  data: FormsetData<TData>;
  toggleItemValue: FormsetChange;
}
function useFormset<TData = object>(
  initial: FormsetData<TData>
): UseFormsetOutput<TData> {
  const [data, setData] = useStateFromProps<FormsetData<TData>>(initial || []);

  function setItemValue(id: string, value: any) {
    const itemIndex = data.findIndex(item => item.id === id);
    setData([
      ...data.slice(0, itemIndex),
      {
        ...data[itemIndex],
        value
      },
      ...data.slice(itemIndex + 1)
    ]);
  }

  function toggleItemValue(id: string, value: any) {
    const itemIndex = data.findIndex(item => item.id === id);
    const field = data[itemIndex];

    if (Array.isArray(field)) {
      setItemValue(id, toggle(value, field, isEqual));
    }
  }

  return {
    change: setItemValue,
    data,
    toggleItemValue
  };
}

export default useFormset;
