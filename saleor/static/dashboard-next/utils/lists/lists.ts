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

export function addAtIndex<TData>(
  data: TData,
  list: List<TData>,
  index: number
) {
  return [...list.slice(0, index), data, ...list.slice(index)];
}

export function move<TData>(
  data: TData,
  list: List<TData>,
  compare: Compare<TData>,
  index: number
) {
  return addAtIndex(data, remove(data, list, compare), index);
}

export function updateAtIndex<TData>(
  data: TData,
  list: List<TData>,
  index: number
) {
  return addAtIndex(data, removeAtIndex(list, index), index);
}

export function remove<TData>(
  data: TData,
  list: List<TData>,
  compare: Compare<TData>
) {
  return list.filter(listElement => !compare(listElement, data));
}

export function removeAtIndex<TData>(list: List<TData>, index: number) {
  return [...list.slice(0, index), ...list.slice(index + 1)];
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
