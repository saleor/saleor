import { useState } from "react";

import useStateFromProps from "./useStateFromProps";

function useModalDialogErrors<TError>(
  errors: TError[],
  open: boolean
): TError[] {
  const [state, setState] = useStateFromProps(errors);
  const [prevOpenState, setPrevOpenstate] = useState(open);

  if (open !== prevOpenState) {
    setPrevOpenstate(open);
    if (!open) {
      setState([]);
    }
  }

  return state;
}

export default useModalDialogErrors;
