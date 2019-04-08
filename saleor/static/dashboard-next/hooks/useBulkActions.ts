import { useEffect } from "react";

import { maybe } from "../misc";
import useListSelector from "./useListSelector";

interface ConnectionNode {
  id: string;
}
function useBulkActions(list: ConnectionNode[]) {
  const listSelectorFuncs = useListSelector();
  useEffect(() => listSelectorFuncs.reset, [
    maybe(() => list.reduce((acc, curr) => acc + curr.id, ""))
  ]);

  return listSelectorFuncs;
}
export default useBulkActions;
