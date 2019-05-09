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
      { id: "1glasses", parentId: "0jewelry", sortOrder: 0, operation: "move" },
      {
        id: "2accessories",
        operation: "move",
        parentId: "3groceries",
        sortOrder: 0
      }
    ],
    [
      { id: "1glasses", parentId: "0jewelry", sortOrder: 0, operation: "move" },
      {
        id: "2accessories",
        operation: "move",
        parentId: "3groceries",
        sortOrder: 0
      },
      {
        id: "3groceries",
        operation: "move",
        parentId: "4apparel",
        sortOrder: 0
      }
    ],
    [
      { id: "0jewelry", sortOrder: 1, operation: "move" },
      { id: "1glasses", sortOrder: 1, operation: "move" },
      {
        id: "4apparel",
        operation: "move",
        parentId: "3groceries",
        sortOrder: 0
      },
      {
        id: "3groceries",
        operation: "move",
        parentId: "0jewelry",
        sortOrder: 0
      },
      { id: "0jewelry", parentId: "1glasses", sortOrder: 0, operation: "move" },
      {
        id: "1glasses",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 0
      },
      { id: "1glasses", sortOrder: 1, operation: "move" },
      { id: "0jewelry", sortOrder: 2, operation: "move" }
    ],
    [
      { id: "1glasses", sortOrder: 1, operation: "move" },
      { id: "1glasses", parentId: "0jewelry", sortOrder: 0, operation: "move" },
      { id: "0jewelry", sortOrder: 1, operation: "move" },
      {
        id: "0jewelry",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 0
      },
      { id: "3groceries", sortOrder: 0, operation: "move" },
      {
        id: "2accessories",
        operation: "move",
        parentId: "3groceries",
        sortOrder: 0
      },
      { id: "2accessories", sortOrder: 1, operation: "move" },
      { id: "0jewelry", sortOrder: 2, operation: "move" },
      { id: "1glasses", sortOrder: 3, operation: "move" },
      { id: "4apparel", sortOrder: 0, operation: "move" },
      { id: "1glasses", sortOrder: 1, operation: "move" },
      { id: "2accessories", sortOrder: 0, operation: "move" },
      {
        id: "4apparel",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 0
      },
      {
        id: "3groceries",
        operation: "move",
        parentId: "1glasses",
        sortOrder: 0
      },
      { id: "0jewelry", sortOrder: 0, operation: "move" },
      {
        id: "0jewelry",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 0
      },
      {
        id: "4apparel",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 0
      },
      {
        id: "0jewelry",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 0
      },
      {
        id: "1glasses",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 2
      },
      {
        id: "0jewelry",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 2
      },
      {
        id: "1glasses",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 2
      },
      {
        id: "4apparel",
        operation: "move",
        parentId: "2accessories",
        sortOrder: 2
      },
      {
        id: "3groceries",
        operation: "move",
        parentId: "0jewelry",
        sortOrder: 0
      },
      { id: "4apparel", parentId: "1glasses", sortOrder: 0, operation: "move" },
      { id: "1glasses", sortOrder: 1, operation: "move" },
      { id: "0jewelry", sortOrder: 1, operation: "move" },
      {
        id: "2accessories",
        operation: "move",
        parentId: "4apparel",
        sortOrder: 0
      }
    ],
    [{ id: "2accessories", operation: "remove" }],
    [
      { id: "2accessories", operation: "remove" },
      { id: "4apparel", operation: "move", sortOrder: 0 },
      { id: "3groceries", operation: "remove" }
    ]
  ];

  testTable.forEach(testData =>
    it("#", () => {
      const computedTree = computeTree(menu.items, testData);
      expect(treeToString(computedTree)).toMatchSnapshot();
    })
  );
});
