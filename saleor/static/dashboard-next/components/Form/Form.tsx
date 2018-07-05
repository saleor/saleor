import * as React from "react";

export interface FormProps<T extends {}> {
  children:
    | ((
        props: {
          data: T;
          hasChanged: boolean;
          change(event: React.ChangeEvent<any>);
          submit(event: React.FormEvent<any>);
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  initial?: T;
  useForm?: boolean;
  onSubmit?(data: T);
}

class Form<T extends {} = {}> extends React.Component<FormProps<T>, T> {
  state: T = this.props.initial;

  handleChange = (event: React.ChangeEvent<any>) => {
    const { target } = event;
    if (!(target.name in this.state)) {
      console.error(`Unknown form field: ${target.name}`);
      return;
    }
    this.setState(({ [target.name]: target.value } as any) as Pick<T, keyof T>);
  };

  handleKeyDown = (event: React.KeyboardEvent<any>) => {
    switch (event.keyCode) {
      // Enter
      case 13:
        this.props.onSubmit(this.state);
        break;
    }
  };

  handleSubmit = (event?: React.FormEvent<any>) => {
    const { onSubmit } = this.props;
    event.preventDefault();
    if (onSubmit !== undefined) {
      onSubmit(this.state);
    }
  };

  render() {
    const { children, useForm = true } = this.props;

    let contents = children;

    if (typeof children === "function") {
      contents = children({
        change: this.handleChange,
        data: this.state,
        hasChanged:
          JSON.stringify(this.props.initial) !== JSON.stringify(this.state),
        submit: this.handleSubmit
      });
    }

    return useForm ? (
      <form onSubmit={this.handleSubmit}>{contents}</form>
    ) : (
      <div onKeyDown={this.handleKeyDown}>{contents}</div>
    );
  }
}

export default Form;
