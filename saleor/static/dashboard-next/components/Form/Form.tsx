import * as React from "react";

export interface FormProps<T extends {}> {
  children:
    | ((
        props: {
          data: T;
          change(event: React.ChangeEvent<any>);
          submit(event: React.FormEvent<any>);
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  initial?: T;
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

  handleSubmit = (event: React.FormEvent<any>) => {
    const { onSubmit } = this.props;
    event.preventDefault();
    if (onSubmit !== undefined) {
      onSubmit(this.state);
    }
  };

  render() {
    const { children } = this.props;

    let contents = children;

    if (typeof children === "function") {
      contents = children({
        change: this.handleChange,
        data: this.state,
        submit: this.handleSubmit
      });
    }

    return <form onSubmit={this.handleSubmit}>{contents}</form>;
  }
}

export default Form;
