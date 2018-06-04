import * as React from "react";

interface DateProviderProps {
  children: ((
    props: {
      date: number;
    }
  ) => React.ReactElement<any>);
}
interface DateProviderState {
  date: number;
  intervalId: number;
}

export class DateProvider extends React.Component<
  DateProviderProps,
  DateProviderState
> {
  constructor(props) {
    super(props);
    const intervalId = setInterval(() => this.setState({ date: Date.now() }));
    this.state = {
      date: Date.now(),
      intervalId
    };
  }

  render() {
    const content = this.props.children({
      date: this.state.date
    });
    return content;
  }
}
