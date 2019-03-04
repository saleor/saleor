import * as React from "react";

export interface AnchorProps {
  children: (anchor: React.RefObject<HTMLDivElement>) => React.ReactNode;
}

class Anchor extends React.Component<AnchorProps> {
  anchor = React.createRef<HTMLDivElement>();

  render() {
    return this.anchor ? this.props.children(this.anchor) : null;
  }
}
export default Anchor;
