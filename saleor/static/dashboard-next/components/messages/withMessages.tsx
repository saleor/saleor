import * as React from "react";

import { IMessage, MessageContext } from ".";

type Omit<T, K> = Pick<T, Exclude<keyof T, K>>;
type Subtract<T, K> = Omit<T, keyof K>;
interface InjectorProps {
  pushMessage: (message: IMessage) => void;
}

export const withMessages = <T extends InjectorProps>(
  Component: React.ComponentType<T>
): React.StatelessComponent<Subtract<T, InjectorProps>> => props => (
  <MessageContext.Consumer>
    {pushMessage => <Component {...props} pushMessage={pushMessage} />}
  </MessageContext.Consumer>
);
export default withMessages;
