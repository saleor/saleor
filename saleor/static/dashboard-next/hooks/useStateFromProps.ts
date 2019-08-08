import isEqual from "lodash-es/isEqual";
import { Dispatch, SetStateAction, useState } from "react";

export interface UseStateFromPropsOpts<T> {
  mergeFunc?: (prevData: T, state: T, newData: T) => T;
  onRefresh?: (data: T) => void;
}

function useStateFromProps<T>(
  data: T,
  opts?: UseStateFromPropsOpts<T>
): [T, Dispatch<SetStateAction<T>>] {
  const [state, setState] = useState(data);
  const [prevData, setPrevData] = useState(data);
  if (!opts) {
    opts = {};
  }

  const { mergeFunc, onRefresh } = opts;
  const shouldUpdate = !isEqual(prevData, data);

  if (shouldUpdate) {
    const newData =
      typeof mergeFunc === "function" ? mergeFunc(prevData, state, data) : data;
    setState(newData);
    setPrevData(data);
    if (typeof onRefresh === "function") {
      onRefresh(newData);
    }
  }

  return [state, setState];
}

export default useStateFromProps;
