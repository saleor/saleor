import * as React from "react";
import { UserError } from "../../types";

export interface FormProps<T extends {}> {
  children: ((
    props: {
      data: T;
      hasChanged: boolean;
      errors: { [key: string]: string };
      change(event: React.ChangeEvent<any>, cb?: () => void);
      submit(event?: React.FormEvent<any>);
    }
  ) => React.ReactElement<any>);
  errors?: UserError[];
  initial?: T;
  confirmLeave?: boolean;
  useForm?: boolean;
  onSubmit?(data: T);
}

interface FormComponentProps<T extends {}> extends FormProps<T> {
  hasChanged: boolean;
  toggleFormChangeState: () => void;
}

interface FormState<T extends {}> {
  initial: T;
  fields: T;
}

class FormComponent<T extends {} = {}> extends React.Component<
  FormComponentProps<T>,
  FormState<T>
> {
  static getDerivedStateFromProps<T extends {} = {}>(
    nextProps: FormComponentProps<T>,
    prevState: FormState<T>
  ): FormState<T> {
    const changedFields = Object.keys(nextProps.initial).filter(
      nextFieldName =>
        JSON.stringify(nextProps.initial[nextFieldName]) !==
        JSON.stringify(prevState.initial[nextFieldName])
    );
    if (changedFields.length > 0) {
      const swapFields = changedFields.reduce((prev, curr) => {
        prev[curr] = nextProps.initial[curr];
        return prev;
      }, {});

      return {
        fields: {
          ...(prevState.fields as any),
          ...swapFields
        },
        initial: {
          ...(prevState.initial as any),
          ...swapFields
        }
      };
    }
    return null;
  }

  state: FormState<T> = {
    fields: this.props.initial,
    initial: this.props.initial
  };

  componentDidUpdate() {
    const { hasChanged, confirmLeave, toggleFormChangeState } = this.props;
    if (this.hasChanged() !== hasChanged && confirmLeave) {
      toggleFormChangeState();
    }
  }

  componentDidMount() {
    const { hasChanged, confirmLeave, toggleFormChangeState } = this.props;
    if (this.hasChanged() !== hasChanged && confirmLeave) {
      toggleFormChangeState();
    }
  }

  componentWillUnmount() {
    const { hasChanged, confirmLeave, toggleFormChangeState } = this.props;
    if (hasChanged && confirmLeave) {
      toggleFormChangeState();
    }
  }

  handleChange = (event: React.ChangeEvent<any>, cb?: () => void) => {
    const { target } = event;
    if (!(target.name in this.state.fields)) {
      console.error(`Unknown form field: ${target.name}`);
      return;
    }

    this.setState(
      {
        fields: {
          ...(this.state.fields as any),
          [target.name]: target.value
        }
      },
      cb
    );
  };

  handleKeyDown = (event: React.KeyboardEvent<any>) => {
    switch (event.keyCode) {
      // Enter
      case 13:
        this.props.onSubmit(this.state.fields);
        break;
    }
  };

  handleSubmit = (event?: React.FormEvent<any>) => {
    const { onSubmit } = this.props;
    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }
    if (onSubmit !== undefined) {
      onSubmit(this.state.fields);
    }
  };

  hasChanged = () =>
    JSON.stringify(this.state.initial) !== JSON.stringify(this.state.fields);

  render() {
    const { children, errors, useForm = true } = this.props;

    const contents = children({
      change: this.handleChange,
      data: this.state.fields,
      errors: errors
        ? errors.reduce(
            (prev, curr) => ({
              ...prev,
              [curr.field.split(":")[0]]: curr.message
            }),
            {}
          )
        : {},
      hasChanged: this.hasChanged(),
      submit: this.handleSubmit
    });

    return useForm ? (
      <form onSubmit={this.handleSubmit}>{contents}</form>
    ) : (
      <div onKeyDown={this.handleKeyDown}>{contents}</div>
    );
  }
}
export default FormComponent;
