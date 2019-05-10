import {
  addNodeUnderParent,
  find,
  insertNode,
  removeNode,
  TreeItem
} from "react-sortable-tree";

import { getDiff } from "./tree";

const originalTree: TreeItem[] = [
  {
    children: [
      { children: [], expanded: true, id: "0jewelry", title: "Jewelry" },
      { children: [], expanded: true, id: "1glasses", title: "Glasses" }
    ],
    expanded: true,
    id: "2accessories",
    title: "Accessories"
  },
  { children: [], expanded: true, id: "3groceries", title: "Groceries" },
  { children: [], expanded: true, id: "4apparel", title: "Apparel" }
];

function getNodeKey(node: any) {
  return node.treeIndex;
}

function moveNode(
  tree: TreeItem[],
  src: string,
  target: string,
  asChild: boolean
) {
  const { matches: srcNodeCandidates } = find({
    getNodeKey,
    searchMethod: ({ node }) => node.id === src,
    treeData: tree
  });
  const srcNodeData = srcNodeCandidates[0];

  const treeAfterRemoval = removeNode({
    getNodeKey,
    path: srcNodeData.path,
    treeData: tree
  }).treeData;

  const { matches: targetNodeCandidates } = find({
    getNodeKey,
    searchMethod: ({ node }) => node.id === target,
    treeData: treeAfterRemoval
  });
  const targetNodeData = targetNodeCandidates[0];

  const treeAfterInsertion = asChild
    ? addNodeUnderParent({
        addAsFirstChild: true,
        getNodeKey,
        ignoreCollapsed: false,
        newNode: srcNodeData.node,
        parentKey: targetNodeData.treeIndex,
        treeData: treeAfterRemoval
      }).treeData
    : insertNode({
        depth: targetNodeData.path.length,
        getNodeKey,
        minimumTreeIndex: targetNodeData.treeIndex,
        newNode: srcNodeData.node,
        treeData: treeAfterRemoval
      }).treeData;

  return treeAfterInsertion as TreeItem[];
}

describe("Properly computes diffs", () => {
  const testTable = [
    moveNode(originalTree, "1glasses", "0jewelry", true),
    moveNode(originalTree, "1glasses", "0jewelry", false),
    moveNode(originalTree, "2accessories", "4apparel", true)
  ];

  testTable.forEach(testData =>
    it("#", () => {
      const diff = getDiff(originalTree, testData);
      expect(diff).toMatchSnapshot();
    })
  );
});
