import React from "react";

import useForm, { UseFormResult } from "@saleor/hooks/useForm";
import { UserError } from "@saleor/types";

export interface FormProps<T> {
  children: (props: UseFormResult<T>) => React.ReactNode;
  confirmLeave?: boolean;
  errors?: UserError[];
  initial?: T;
  resetOnSubmit?: boolean;
  onSubmit?: (data: T) => void;
}

function Form<T>(props: FormProps<T>) {
  const { children, errors, initial, resetOnSubmit, onSubmit } = props;
  const renderProps = useForm(initial, errors, onSubmit);

  function handleSubmit(event?: React.FormEvent<any>, cb?: () => void) {
    const { reset, submit } = renderProps;

    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }

    if (cb) {
      cb();
    }

    if (resetOnSubmit) {
      reset();
    }

    submit();
  }

  return <form onSubmit={handleSubmit}>{children(renderProps)}</form>;
}
Form.displayName = "Form";

export default Form;
