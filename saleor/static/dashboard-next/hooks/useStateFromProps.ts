import isEqual from "lodash-es/isEqual";
import { Dispatch, SetStateAction, useEffect, useState } from "react";

function useStateFromProps<T>(data: T): [T, Dispatch<SetStateAction<T>>] {
  const [state, setState] = useState(data);
  const [prevState, setPrevState] = useState(data);

  useEffect(() => {
    setState(data);
    setPrevState(data);
  }, [!isEqual(prevState, data)]);

  return [state, setState];
}

export default useStateFromProps;
