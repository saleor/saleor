import { menu } from "../../fixtures";
import { MenuDetails_menu_items } from "../../types/MenuDetails";
import { TreeOperation } from "../MenuItems";
import { computeTree } from "./tree";

// Readability FTW
function innerTreeToString(
  tree: MenuDetails_menu_items,
  level: number
): string {
  return (
    "\n" +
    "··".repeat(level) +
    tree.name +
    tree.children.reduce(
      (acc, node) => acc + innerTreeToString(node, level + 1),
      ""
    )
  );
}
function treeToString(tree: MenuDetails_menu_items[]): string {
  return tree.reduce((acc, node) => acc + innerTreeToString(node, 0), "");
}

describe("Properly computes trees", () => {
  const testTable: TreeOperation[][] = [
    [],
    [
      { id: "1glasses", parentId: "0jewelry", sortOrder: 0, type: "move" },
      {
        id: "2accessories",
        parentId: "3groceries",
        sortOrder: 0,
        type: "move"
      }
    ],
    [
      { id: "1glasses", parentId: "0jewelry", sortOrder: 0, type: "move" },
      {
        id: "2accessories",
        parentId: "3groceries",
        sortOrder: 0,
        type: "move"
      },
      {
        id: "3groceries",
        parentId: "4apparel",
        sortOrder: 0,
        type: "move"
      }
    ],
    [
      { id: "0jewelry", sortOrder: 1, type: "move" },
      { id: "1glasses", sortOrder: 1, type: "move" },
      {
        id: "4apparel",
        parentId: "3groceries",
        sortOrder: 0,
        type: "move"
      },
      {
        id: "3groceries",
        parentId: "0jewelry",
        sortOrder: 0,
        type: "move"
      },
      { id: "0jewelry", parentId: "1glasses", sortOrder: 0, type: "move" },
      {
        id: "1glasses",
        parentId: "2accessories",
        sortOrder: 0,
        type: "move"
      },
      { id: "1glasses", sortOrder: 1, type: "move" },
      { id: "0jewelry", sortOrder: 2, type: "move" }
    ],
    [
      { id: "1glasses", sortOrder: 1, type: "move" },
      { id: "1glasses", parentId: "0jewelry", sortOrder: 0, type: "move" },
      { id: "0jewelry", sortOrder: 1, type: "move" },
      {
        id: "0jewelry",
        parentId: "2accessories",
        sortOrder: 0,
        type: "move"
      },
      { id: "3groceries", sortOrder: 0, type: "move" },
      {
        id: "2accessories",
        parentId: "3groceries",
        sortOrder: 0,
        type: "move"
      },
      { id: "2accessories", sortOrder: 1, type: "move" },
      { id: "0jewelry", sortOrder: 2, type: "move" },
      { id: "1glasses", sortOrder: 3, type: "move" },
      { id: "4apparel", sortOrder: 0, type: "move" },
      { id: "1glasses", sortOrder: 1, type: "move" },
      { id: "2accessories", sortOrder: 0, type: "move" },
      {
        id: "4apparel",
        parentId: "2accessories",
        sortOrder: 0,
        type: "move"
      },
      {
        id: "3groceries",
        parentId: "1glasses",
        sortOrder: 0,
        type: "move"
      },
      { id: "0jewelry", sortOrder: 0, type: "move" },
      {
        id: "0jewelry",
        parentId: "2accessories",
        sortOrder: 0,
        type: "move"
      },
      {
        id: "4apparel",
        parentId: "2accessories",
        sortOrder: 0,
        type: "move"
      },
      {
        id: "0jewelry",
        parentId: "2accessories",
        sortOrder: 0,
        type: "move"
      },
      {
        id: "1glasses",
        parentId: "2accessories",
        sortOrder: 2,
        type: "move"
      },
      {
        id: "0jewelry",
        parentId: "2accessories",
        sortOrder: 2,
        type: "move"
      },
      {
        id: "1glasses",
        parentId: "2accessories",
        sortOrder: 2,
        type: "move"
      },
      {
        id: "4apparel",
        parentId: "2accessories",
        sortOrder: 2,
        type: "move"
      },
      {
        id: "3groceries",
        parentId: "0jewelry",
        sortOrder: 0,
        type: "move"
      },
      { id: "4apparel", parentId: "1glasses", sortOrder: 0, type: "move" },
      { id: "1glasses", sortOrder: 1, type: "move" },
      { id: "0jewelry", sortOrder: 1, type: "move" },
      {
        id: "2accessories",
        parentId: "4apparel",
        sortOrder: 0,
        type: "move"
      }
    ],
    [{ id: "2accessories", type: "remove" }],
    [
      { id: "2accessories", type: "remove" },
      { id: "4apparel", type: "move", sortOrder: 0 },
      { id: "3groceries", type: "remove" }
    ]
  ];

  testTable.forEach(testData =>
    it("#", () => {
      const computedTree = computeTree(menu.items, testData);
      expect(treeToString(computedTree)).toMatchSnapshot();
    })
  );
});
