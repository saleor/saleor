import isEqual from "lodash-es/isEqual";
import { useState } from "react";

import { UserError } from "@saleor/types";
import { toggle } from "@saleor/utils/lists";
import useStateFromProps from "./useStateFromProps";

export interface ChangeEvent<TData = any> {
  target: {
    name: string;
    value: TData;
  };
}

export type FormChange = (event: ChangeEvent, cb?: () => void) => void;

export interface UseFormResult<T> {
  change: FormChange;
  data: T;
  errors: Record<string, string>;
  hasChanged: boolean;
  reset: () => void;
  set: (data: T) => void;
  submit: () => void;
  triggerChange: () => void;
  toggleValue: FormChange;
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

  function toggleValue(event: ChangeEvent, cb?: () => void) {
    const { name, value } = event.target;
    const field = data[name as keyof T];

    if (Array.isArray(field)) {
      if (!hasChanged) {
        setChanged(true);
      }
      setData({
        ...data,
        [name]: toggle(value, field, isEqual)
      });
    }

    if (typeof cb === "function") {
      cb();
    }
  }

  function change(event: ChangeEvent) {
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
  }

  function reset() {
    setData(initial);
  }

  function set(newData: Partial<T>) {
    setData({
      ...data,
      ...newData
    });
  }

  function submit() {
    return onSubmit(data);
  }

  function triggerChange() {
    setChanged(true);
  }

  return {
    change,
    data,
    errors: parseErrors(errors),
    hasChanged,
    reset,
    set,
    submit,
    toggleValue,
    triggerChange
  };
}

export default useForm;
