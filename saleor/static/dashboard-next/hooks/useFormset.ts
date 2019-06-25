import { useEffect, useState } from "react";

export interface FormsetAtomicData<TData = object> {
  data: TData;
  id: string;
  label: string;
  value: string;
}
export type FormsetData<TData = object> = Array<FormsetAtomicData<TData>>;
export interface UseFormsetOutput<TData = object> {
  change: (id: string, value: string) => void;
  data: FormsetData<TData>;
}
function useFormset<TData = object>(
  initial: FormsetData<TData>
): UseFormsetOutput<TData> {
  const [data, setData] = useState<FormsetData<TData>>(initial || []);

  // Reload formset after fetching new initial data
  useEffect(() => setData(initial), [JSON.stringify(initial)]);

  function setItemValue(id: string, value: string) {
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

  return {
    change: setItemValue,
    data
  };
}

export default useFormset;
