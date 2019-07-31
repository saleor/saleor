import { maybe } from "@saleor/misc";
import { UserError } from "@saleor/types";

export function getFieldError(errors: UserError[], field: string): string {
  const err = errors.find(err => err.field === field);

  return maybe(() => err.message);
}

export function getErrors(errors: UserError[]): string[] {
  return errors
    .filter(err => ["", null].includes(err.field))
    .map(err => err.message);
}
