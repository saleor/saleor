import { useContext } from "react";

import { IMessageContext, MessageContext } from "../components/messages";

export type UseNotifierResult = IMessageContext;
function useNotifier(): UseNotifierResult {
  const notify = useContext(MessageContext);
  return notify;
}
export default useNotifier;
