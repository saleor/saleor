import * as React from "react";

import FormComponent, { FormProps } from "./Form";

interface IFormContext {
  hasChanged: boolean;
  toggle: () => void;
}

export const FormContext = React.createContext<IFormContext>(undefined);

interface FormProviderState {
  hasChanged: boolean;
}

export class FormProvider extends React.Component<{}, FormProviderState> {
  state: FormProviderState = {
    hasChanged: false
  };

  toggle = () =>
    this.setState(prevState => ({
      hasChanged: !prevState.hasChanged
    }));

  render() {
    return (
      <FormContext.Provider
        value={{
          hasChanged: this.state.hasChanged,
          toggle: this.toggle
        }}
      >
        {this.props.children}
      </FormContext.Provider>
    );
  }
}

export function Form<T>(props: FormProps<T>) {
  return (
    <FormContext.Consumer>
      {({ hasChanged, toggle }) => (
        <FormComponent
          {...props}
          toggleFormChangeState={toggle}
          hasChanged={hasChanged}
        />
      )}
    </FormContext.Consumer>
  );
}

export default Form;
