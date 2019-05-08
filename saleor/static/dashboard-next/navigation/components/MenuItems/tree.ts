import { getPatch } from "fast-array-diff";
import { TreeItem } from "react-sortable-tree";

import { MenuDetails_menu_items } from "../../types/MenuDetails";

export interface TreePermutation {
  id: string;
  operation: "move" | "remove";
  parentId?: string;
  sortOrder?: number;
}

export type TreeNode = TreeItem & { id: string };

function treeToMap(tree: TreeNode[], parent: string): Record<string, string[]> {
  const childrenList = tree.map(node => node.id);
  const childrenMaps = tree.map(node => ({
    id: node.id,
    mappedNodes: treeToMap(node.children as TreeNode[], node.id)
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

export function getDiff(
  originalTree: TreeNode[],
  newTree: TreeNode[]
): TreePermutation {
  const originalMap = treeToMap(originalTree, "root");
  const newMap = treeToMap(newTree, "root");

  const diff: TreePermutation[] = Object.keys(newMap).map(key => {
    const originalNode = originalMap[key];
    const newNode = newMap[key];

    const patch = getPatch(originalNode, newNode);

    if (patch.length > 0) {
      const addedNode = patch.find(operation => operation.type === "add");
      if (!!addedNode) {
        return {
          id: addedNode.items[0],
          operation: "move",
          parentId: key === "root" ? undefined : key,
          sortOrder: addedNode.newPos
        };
      }
    }
  });

  return diff.find(d => !!d);
}

export function getNodeData(
  item: MenuDetails_menu_items,
  onChange: (operation: TreePermutation) => void
): TreeNode {
  return {
    children: item.children.map(child => getNodeData(child, onChange)),
    expanded: true,
    id: item.id,
    onChange,
    title: item.name
  };
}

export function getNodeQuantity(items: MenuDetails_menu_items[]): number {
  return items.reduce(
    (acc, curr) => acc + getNodeQuantity(curr.children),
    items.length
  );
}
