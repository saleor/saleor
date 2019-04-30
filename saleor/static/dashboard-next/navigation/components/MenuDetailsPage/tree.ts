import { MenuDetails_menu_items } from "../../types/MenuDetails";
import { TreePermutation } from "../MenuItems";

function findNode(tree: MenuDetails_menu_items[], id: string): number[] {
  const foundNodeIndex = tree.findIndex(node => node.id === id);
  if (tree.length === 0) {
    return null;
  }
  if (foundNodeIndex !== -1) {
    return [foundNodeIndex];
  }
  const nodeMap = tree.map((node, nodeIndex) => [
    nodeIndex,
    ...findNode(node.children, id)
  ]);
  return nodeMap.find(path => path[path.length - 1] !== null) || [null];
}

function getNode(
  tree: MenuDetails_menu_items[],
  path: number[]
): MenuDetails_menu_items {
  if (path.length === 1) {
    return tree[path[0]];
  }
  return getNode([...tree[path[0]].children], path.slice(1));
}

function removeNode(
  tree: MenuDetails_menu_items[],
  path: number[]
): MenuDetails_menu_items[] {
  if (path.length === 1) {
    const removeIndex = path[0];
    return [...tree.slice(0, removeIndex), ...tree.slice(removeIndex + 1)];
  }
  tree[path[0]].children = removeNode(tree[path[0]].children, path.slice(1));
  return tree;
}

function insertNode(
  tree: MenuDetails_menu_items[],
  path: number[],
  node: MenuDetails_menu_items,
  position: number
): MenuDetails_menu_items[] {
  if (path.length === 0) {
    return [...tree.slice(0, position), node, ...tree.slice(position)];
  }

  tree[path[0]].children = insertNode(
    tree[path[0]].children,
    path.slice(1),
    node,
    position
  );
  return tree;
}

function permuteNode(
  tree: MenuDetails_menu_items[],
  permutation: TreePermutation
): MenuDetails_menu_items[] {
  const sourcePath = findNode(tree, permutation.id);
  const node = getNode(tree, sourcePath);

  const treeAfterRemoval = removeNode(tree, sourcePath);

  const targetPath = permutation.parentId
    ? findNode(treeAfterRemoval, permutation.parentId)
    : [];

  const treeAfterInsertion = insertNode(
    treeAfterRemoval,
    targetPath,
    node,
    permutation.sortOrder
  );

  return treeAfterInsertion;
}

export function computeTree(
  tree: MenuDetails_menu_items[],
  permutations: TreePermutation[]
) {
  //   console.log(JSON.stringify(permutations));
  const newTree = permutations.reduce(
    (acc, permutation) => permuteNode(acc, permutation),
    JSON.parse(JSON.stringify(tree))
  );
  return newTree;
}
