import * as React from "react";

export interface DebounceProps {
  children: ((props: () => void) => React.ReactNode);
  debounceFn: (event: React.FormEvent<any>) => void;
  time?: number;
}

export class Debounce extends React.Component<DebounceProps> {
  timer = null;

  handleDebounce = () => {
    const { debounceFn, time } = this.props;
    if (this.timer) {
      clearTimeout(this.timer);
    }
    this.timer = setTimeout(debounceFn, time || 200);
  };

  render() {
    return this.props.children(this.handleDebounce);
  }
}
export default Debounce;
