import { parse, stringify } from "qs";

export const screenSizes = {
  sm: 600,
  md: 992,
  lg: 1200
};

export function createQueryString(currentQs, newData) {
  const currentData = parse(currentQs.substr(1));
  const data = stringify({...currentData, ...newData});
  return `?${data}`;
}
