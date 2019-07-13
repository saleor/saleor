type List<TData> = TData[];
type Compare<TData> = (a: TData, b: TData) => boolean;

export function isSelected<TData>(
  data: TData,
  list: List<TData>,
  compare: Compare<TData>
) {
  return !!list.find(listElement => compare(listElement, data));
}

export function add<TData>(data: TData, list: List<TData>) {
  return [...list, data];
}

export function remove<TData>(
  data: TData,
  list: List<TData>,
  compare: Compare<TData>
) {
  return list.filter(listElement => !compare(listElement, data));
}

export function toggle<TData>(
  data: TData,
  list: List<TData>,
  compare: Compare<TData>
) {
  return isSelected(data, list, compare)
    ? remove(data, list, compare)
    : add(data, list);
}
