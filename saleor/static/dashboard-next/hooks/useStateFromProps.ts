import isEqual from "lodash-es/isEqual";
import { Dispatch, SetStateAction, useState } from "react";

function useStateFromProps<T>(data: T): [T, Dispatch<SetStateAction<T>>] {
  const [state, setState] = useState(data);
  const [prevState, setPrevState] = useState(data);

  if (!isEqual(prevState, data)) {
    setState(data);
    setPrevState(data);
  }

  return [state, setState];
}

export default useStateFromProps;
