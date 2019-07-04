import { useContext } from "react";

import { IMessageContext, MessageContext } from "@saleor/components/messages";

export type UseNotifierResult = IMessageContext;
function useNotifier(): UseNotifierResult {
  const notify = useContext(MessageContext);
  return notify;
}
export default useNotifier;
