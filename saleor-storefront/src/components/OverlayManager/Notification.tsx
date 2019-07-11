import * as React from "react";

import { Message, OverlayContextInterface } from "..";

export const NotificationOverlay: React.FC<{
  overlay: OverlayContextInterface;
}> = ({ overlay: { hide, context } }) => {
  return (
    <Message title={context.title} status={context.status} onClose={hide}>
      {context.content}
    </Message>
  );
};

export default NotificationOverlay;
