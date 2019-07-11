import * as React from "react";

export interface DebounceChangeProps<TValue> {
  children: ((
    props: {
      change: (event: React.ChangeEvent<any>) => void;
      value: TValue;
    }
  ) => React.ReactElement<any>);
  debounce: (event: React.ChangeEvent<any>) => void;
  time?: number;
  value: TValue;
  resetValue?: boolean;
}

export interface DebounceChangeState<TValue> {
  timer: any | null;
  value: TValue;
}

export class DebounceChange<TValue> extends React.Component<
  DebounceChangeProps<TValue>,
  DebounceChangeState<TValue>
> {
  static getDerivedStateFromProps(
    props: DebounceChangeProps<any>,
    state: DebounceChangeState<any>
  ) {
    const { resetValue, value: propsValue } = props;
    const { timer, value: stateValue } = state;

    if (resetValue) {
      if (timer) {
        clearTimeout(timer);
      }
      return { value: propsValue, timer };
    }

    if (propsValue !== stateValue && timer === null) {
      return { value: propsValue };
    }

    return null;
  }

  state: DebounceChangeState<TValue> = { timer: null, value: this.props.value };

  handleChange = (event: React.ChangeEvent<any>) => {
    event.persist();
    const { timer } = this.state;

    if (timer) {
      clearTimeout(timer);
    }

    this.setState({
      timer: setTimeout(
        () => this.props.debounce(event),
        this.props.time || 200
      ),
      value: event.target.value,
    });
  };

  render() {
    return this.props.children({
      change: this.handleChange,
      value: this.state.value,
    });
  }
}

export default DebounceChange;
