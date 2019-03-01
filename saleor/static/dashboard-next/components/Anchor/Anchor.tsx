import * as React from "react";

export interface AnchorProps extends React.HTMLAttributes<HTMLDivElement> {
  children: (anchor: React.RefObject<HTMLDivElement>) => React.ReactNode;
}

class Anchor extends React.Component<AnchorProps> {
  anchor = React.createRef<HTMLDivElement>();

  render() {
    return (
      <div ref={this.anchor} {...this.props}>
        {this.props.children(this.anchor)}
      </div>
    );
  }
}
export default Anchor;
