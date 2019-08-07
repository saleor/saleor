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
        (acc, curr) =>
          curr.field
            ? {
                ...acc,
                [curr.field.split(":")[0]]: curr.message
              }
            : acc,
        {}
      )
    : {};
}

type FormData = Record<string, any | any[]>;

function merge<T extends FormData>(prevData: T, prevState: T, data: T): T {
  return Object.keys(prevState).reduce(
    (acc, key) => {
      if (!isEqual(data[key], prevData[key])) {
        acc[key as keyof T] = data[key];
      }

      return acc;
    },
    { ...prevState }
  );
}

function handleRefresh<T extends FormData>(
  data: T,
  newData: T,
  setChanged: (status: boolean) => void
) {
  if (isEqual(data, newData)) {
    setChanged(false);
  }
}

function useForm<T extends FormData>(
  initial: T,
  errors: UserError[],
  onSubmit: (data: T) => void
): UseFormResult<T> {
  const [hasChanged, setChanged] = useState(false);
  const [data, setData] = useStateFromProps(initial, {
    mergeFunc: merge,
    onRefresh: newData => handleRefresh(data, newData, setChanged)
  });

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
