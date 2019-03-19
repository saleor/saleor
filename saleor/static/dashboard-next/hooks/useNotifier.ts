import { useContext } from "react";

import { MessageContext } from "../components/messages";

function useNotifier() {
  const notify = useContext(MessageContext);
  return notify;
}
export default useNotifier;
