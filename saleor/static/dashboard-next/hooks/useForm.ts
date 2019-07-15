import isEqual from "lodash-es/isEqual";
import { useState } from "react";

import { UserError } from "@saleor/types";
import { toggle } from "@saleor/utils/lists";
import useStateFromProps from "./useStateFromProps";

export interface ChangeEvent<TName = string, TData = any> {
  target: {
    name: keyof TName | string;
    value: TData;
  };
}

export interface UseFormResult<T> {
  change: (event: ChangeEvent<T>, cb?: () => void) => void;
  data: T;
  errors: Record<string, string>;
  hasChanged: boolean;
  reset: () => void;
  set: (data: T) => void;
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

function useForm<T extends Record<string, any | any[]>>(
  initial: T,
  errors: UserError[],
  onSubmit: (data: T) => void
): UseFormResult<T> {
  const [hasChanged, setChanged] = useState(false);
  const [data, setData] = useStateFromProps(initial, () => setChanged(false));

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

  function change(event: ChangeEvent<T>) {
    const { name, value } = event.target;

    if (!(name in data)) {
      console.error(`Unknown form field: ${name}`);
      return;
    } else {
      if (data[name] !== value) {
        setChanged(true);
      }
      setData(data => ({
        ...data,
        [name]: value
      }));
    }
  }

  function reset() {
    setData(initial);
  }

  function set(newData: Partial<T>) {
    setData(data => ({
      ...data,
      ...newData
    }));
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
    set,
    submit,
    toggleValue
  };
}

export default useForm;
