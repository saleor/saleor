export interface IMenu<TData = {}> {
  children?: Array<IMenu<TData>>;
  data?: TData;
  label: React.ReactNode;
  value?: string;
}

function getMenuOptionValues(menuOption: IMenu): string[] {
  return menuOption.value
    ? [menuOption.value]
    : menuOption.children.reduce(
        (acc, menuOption) => [...acc, ...getMenuOptionValues(menuOption)],
        []
      );
}

export function validateMenuOptions(menuOptions: IMenu[]): boolean {
  const values: string[] = menuOptions.reduce(
    (acc, menuOption) => [...acc, ...getMenuOptionValues(menuOption)],
    []
  );
  const uniqueValues = Array.from(new Set(values));
  return uniqueValues.length === values.length;
}

export function getMenu(menuOptions: IMenu[], path: number[]): IMenu[] {
  if (path.length === 0) {
    return menuOptions;
  }
  return getMenu(menuOptions[path[0]].children, path.slice(1));
}
