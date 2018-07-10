import { createContext } from "react";

export interface IMessage {
  text: string;
  onUndo?: () => void;
}
export const MessageContext = createContext((message: IMessage) => {});

export * from "./MessageManager";
export default MessageContext.Consumer;
