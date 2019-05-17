import { getPatch } from "fast-array-diff";
import { TreeItem } from "react-sortable-tree";

import { MenuDetails_menu_items } from "../../types/MenuDetails";
import { MenuItemType } from "../MenuItemDialog";

export type TreeOperationType = "move" | "remove";
export interface TreeOperation {
  id: string;
  type: TreeOperationType;
  parentId?: string;
  sortOrder?: number;
}

export const unknownTypeError = Error("Unknown type");

function treeToMap(tree: TreeItem[], parent: string): Record<string, string[]> {
  const childrenList = tree.map(node => node.id);
  const childrenMaps = tree.map(node => ({
    id: node.id,
    mappedNodes: treeToMap(node.children as TreeItem[], node.id)
  }));

  return {
    [parent]: childrenList,
    ...childrenMaps.reduce(
      (acc, childMap) => ({
        ...acc,
        ...childMap.mappedNodes
      }),
      {}
    )
  };
}

export function getItemType(item: MenuDetails_menu_items): MenuItemType {
  if (item.category) {
    return "category";
  } else if (item.collection) {
    return "collection";
  } else if (item.page) {
    return "page";
  } else if (item.url) {
    return "link";
  } else {
    throw unknownTypeError;
  }
}

export function getItemId(item: MenuDetails_menu_items): string {
  if (item.category) {
    return item.category.id;
  } else if (item.collection) {
    return item.collection.id;
  } else if (item.page) {
    return item.page.id;
  } else if (item.url) {
    return item.url;
  } else {
    throw unknownTypeError;
  }
}

export function getDiff(
  originalTree: TreeItem[],
  newTree: TreeItem[]
): TreeOperation {
  const originalMap = treeToMap(originalTree, "root");
  const newMap = treeToMap(newTree, "root");

  const diff: TreeOperation[] = Object.keys(newMap).map(key => {
    const originalNode = originalMap[key];
    const newNode = newMap[key];

    const patch = getPatch(originalNode, newNode);

    if (patch.length > 0) {
      const addedNode = patch.find(operation => operation.type === "add");
      if (!!addedNode) {
        return {
          id: addedNode.items[0],
          parentId: key === "root" ? undefined : key,
          sortOrder: addedNode.newPos,
          type: "move" as TreeOperationType
        };
      }
    }
  });

  return diff.find(d => !!d);
}

export function getNodeData(
  item: MenuDetails_menu_items,
  onChange: (operation: TreeOperation) => void,
  onClick: (id: string, type: MenuItemType) => void,
  onEdit: (id: string) => void
): TreeItem {
  return {
    children: item.children.map(child =>
      getNodeData(child, onChange, onClick, onEdit)
    ),
    expanded: true,
    id: item.id,
    onChange,
    onClick: () => onClick(getItemId(item), getItemType(item)),
    onEdit: () => onEdit(item.id),
    title: item.name
  };
}

export function getNodeQuantity(items: MenuDetails_menu_items[]): number {
  return items.reduce(
    (acc, curr) => acc + getNodeQuantity(curr.children),
    items.length
  );
}
