import isEqual from "lodash-es/isEqual";
import { useState } from "react";

import { UserError } from "@saleor/types";
import { toggle } from "@saleor/utils/lists";
import useStateFromProps from "./useStateFromProps";

interface ChangeEvent<T> {
  target: {
    name: keyof T | string;
    value: any;
  };
}

export interface UseFormResult<T> {
  change: (event: ChangeEvent<T>, cb?: () => void) => void;
  data: T;
  errors: Record<string, string>;
  hasChanged: boolean;
  reset: () => void;
  submit: () => void;
  toggleValue: (event: ChangeEvent<T>) => void;
}

function parseErrors(errors: UserError[]): Record<string, string> {
  return errors
    ? errors.reduce(
        (prev, curr) => ({
          ...prev,
          [curr.field.split(":")[0]]: curr.message
        }),
        {}
      )
    : {};
}

function useForm<T extends Record<keyof T, any | any[]>>(
  initial: T,
  errors: UserError[],
  onSubmit: (data: T) => void
): UseFormResult<T> {
  const [data, setData] = useStateFromProps(initial);
  const [hasChanged, setChanged] = useState(false);

  function toggleValue(event: ChangeEvent<T>) {
    const { name, value } = event.target;
    const field = data[name as keyof T];

    if (Array.isArray(field)) {
      setData({
        ...data,
        [name]: toggle(value, field, isEqual)
      });
    }
  }

  function change(event: ChangeEvent<T>, cb?: () => void) {
    const { name, value } = event.target;

    if (!(name in data)) {
      console.error(`Unknown form field: ${name}`);
      return;
    }

    if (!hasChanged) {
      setChanged(true);
    }
    setData({
      ...data,
      [name]: value
    });
    if (typeof cb === "function") {
      cb();
    }
  }

  function reset() {
    setData(initial);
  }

  function submit() {
    return onSubmit(data);
  }

  return {
    change,
    data,
    errors: parseErrors(errors),
    hasChanged,
    reset,
    submit,
    toggleValue
  };
}

export default useForm;
