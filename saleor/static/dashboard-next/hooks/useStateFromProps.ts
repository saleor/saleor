import isEqual from "lodash-es/isEqual";
import { Dispatch, SetStateAction, useState } from "react";

function useStateFromProps<T>(
  data: T,
  onRefresh?: (data: T) => void
): [T, Dispatch<SetStateAction<T>>] {
  const [state, setState] = useState(data);
  const [prevProps, setPrevProps] = useState(data);

  if (!isEqual(prevProps, data)) {
    setState(data);
    setPrevProps(data);
    if (typeof data === "function") {
      onRefresh(data);
    }
  }

  return [state, setState];
}

export default useStateFromProps;
