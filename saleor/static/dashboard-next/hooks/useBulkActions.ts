import { useEffect } from "react";

import useListSelector from "./useListSelector";

interface ConnectionNode {
  id: string;
}
function useBulkActions(list: ConnectionNode[]) {
  const listSelectorFuncs = useListSelector();
  useEffect(() => listSelectorFuncs.reset, [list === undefined, list === null]);

  return listSelectorFuncs;
}
export default useBulkActions;
