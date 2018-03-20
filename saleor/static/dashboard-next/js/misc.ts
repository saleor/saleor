import { parse, stringify } from "qs";

export function createQueryString(currentQs, newData) {
  const currentData = parse(currentQs.substr(1));
  const data = stringify({ ...currentData, ...newData });
  return `?${data}`;
}
