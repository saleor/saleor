import { createContext } from "react";

export interface IMessage {
  text: string;
  onUndo?: () => void;
}
export const MessageContext = createContext((message => {}) as (
  message: IMessage
) => void);

export * from "./MessageManager";
export * from "./withMessages";
export { default } from "./withMessages";
