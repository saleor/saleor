import * as React from "react";

interface ChoiceProviderProps {
  children:
    | ((
        props: {
          choices: Array<{
            label?: React.ReactNode;
            name: string;
            value: string;
          }>;
          loading: boolean;
          fetchChoices(value: string);
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  choices: Array<{
    label?: React.ReactNode;
    name: string;
    value: string;
  }>;
}
interface ChoiceProviderState {
  choices: Array<{
    label?: React.ReactNode;
    name: string;
    value: string;
  }>;
  loading: boolean;
  timeout: any;
}

export class ChoiceProvider extends React.Component<
  ChoiceProviderProps,
  ChoiceProviderState
> {
  state = { choices: [], loading: false, timeout: null };

  handleChange = (inputValue: string) => {
    if (this.state.loading) {
      clearTimeout(this.state.timeout);
    }
    const timeout = setTimeout(() => this.fetchChoices(inputValue), 500);
    this.setState({
      loading: true,
      timeout
    });
  };

  fetchChoices = (inputValue: string) => {
    let count = 0;
    this.setState({
      choices: this.props.choices.filter(suggestion => {
        const keep =
          (!inputValue ||
            suggestion.name.toLowerCase().indexOf(inputValue.toLowerCase()) !==
              -1) &&
          count < 5;

        if (keep) {
          count += 1;
        }

        return keep;
      }),
      loading: false,
      timeout: null
    });
  };

  render() {
    if (typeof this.props.children === "function") {
      return this.props.children({
        choices: this.state.choices,
        fetchChoices: this.handleChange,
        loading: this.state.loading
      });
    }
    return this.props.children;
  }
}
