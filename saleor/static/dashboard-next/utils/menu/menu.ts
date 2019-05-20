interface IBaseMenuItem<TMenuData = {}> {
  label: React.ReactNode;
  value?: string;
  data: TMenuData | null;
}
export type IFlatMenuItem<TMenuData = {}> = IBaseMenuItem<TMenuData> & {
  id: string;
  parent: string | null;
  sort: number;
};
export type IMenuItem<TMenuData = {}> = IBaseMenuItem<TMenuData> & {
  children: Array<IMenuItem<TMenuData>>;
};
export type IMenu<TMenuData = {}> = Array<IMenuItem<TMenuData>>;
export type IFlatMenu<TMenuData = {}> = Array<IFlatMenuItem<TMenuData>>;

export function validateMenuOptions<TMenuData = {}>(
  menu: IMenu<TMenuData>
): boolean {
  const values: string[] = toFlat(menu)
    .map(menuItem => menuItem.value)
    .filter(value => value !== undefined);
  const uniqueValues = Array.from(new Set(values));
  return uniqueValues.length === values.length;
}

function _getMenuItemByPath<TMenuData = {}>(
  menuItem: IMenuItem<TMenuData>,
  path: number[]
): IMenuItem<TMenuData> {
  if (path.length === 0) {
    return menuItem;
  }
  return _getMenuItemByPath(menuItem.children[path[0]], path.slice(1));
}

export function getMenuItemByPath<TMenuData = {}>(
  menu: IMenu<TMenuData>,
  path: number[]
): IMenuItem<TMenuData> {
  return _getMenuItemByPath(menu[path[0]], path.slice(1));
}

export function getMenuItemByValue<TMenuData = {}>(
  menu: IMenu<TMenuData>,
  value: string
): IMenuItem<TMenuData> {
  const flatMenu = toFlat(menu);
  const flatMenuItem: IFlatMenuItem<TMenuData> = flatMenu.find(
    menuItem => menuItem.value === value
  );

  return _fromFlat(flatMenu, flatMenuItem.id);
}

function _walkToMenuItem<TMenuData = {}>(
  menuItem: IMenuItem<TMenuData>,
  path: number[]
): IMenu<TMenuData> {
  const node = menuItem.children[path[0]];

  if (path.length === 1) {
    return [node];
  }

  return [node, ..._walkToMenuItem(node, path.slice(1))];
}

export function walkToMenuItem<TMenuData = {}>(
  menu: IMenu<TMenuData>,
  path: number[]
): IMenu<TMenuData> {
  const walkByNode = menu[path[0]];
  return [walkByNode, ..._walkToMenuItem(walkByNode, path.slice(1))];
}

function _toFlat<TMenuData = {}>(
  menuItem: IMenuItem<TMenuData>,
  sort: number,
  parent: string
): IFlatMenu<TMenuData> {
  const id = parent ? [parent, sort].join(":") : sort.toString();
  const flatMenuItem: IFlatMenuItem<TMenuData> = {
    data: menuItem.data,
    id,
    label: menuItem.label,
    parent,
    sort,
    value: menuItem.value
  };
  return [
    flatMenuItem,
    ...menuItem.children
      .map((child, childIndex) => _toFlat(child, childIndex, id))
      .reduce((acc, curr) => [...acc, ...curr], [] as IFlatMenu<TMenuData>)
  ];
}
export function toFlat<TMenuData = {}>(
  menu: IMenu<TMenuData>
): IFlatMenu<TMenuData> {
  return menu
    .map((menuItem, menuItemIndex) => _toFlat(menuItem, menuItemIndex, null))
    .reduce((acc, curr) => [...acc, ...curr], [] as IFlatMenu<TMenuData>);
}

function _fromFlat<TMenuData = {}>(
  menu: IFlatMenu<TMenuData>,
  id: string
): IMenuItem<TMenuData> {
  const flatMenuItem = menu.find(menuItem => menuItem.id === id);
  const children: Array<IMenuItem<TMenuData>> = menu
    .filter(menuItem => menuItem.parent === flatMenuItem.id)
    .map(menuItem => _fromFlat(menu, menuItem.id));

  return {
    children,
    data: flatMenuItem.data,
    label: flatMenuItem.label,
    value: flatMenuItem.value
  };
}
export function fromFlat<TMenuData = {}>(
  menu: IFlatMenu<TMenuData>
): IMenu<TMenuData> {
  return menu
    .filter(menuItem => menuItem.parent === null)
    .map(menuItem => _fromFlat(menu, menuItem.id));
}
