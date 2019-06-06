import {
  fromFlat,
  getMenuItemByPath,
  getMenuItemByValue,
  IMenu,
  toFlat,
  validateMenuOptions,
  walkToMenuItem,
  walkToRoot
} from "./menu";

const validMenu: IMenu = [
  {
    children: [],
    data: null,
    label: "1",
    value: "1"
  },
  {
    children: [],
    data: null,
    label: "2",
    value: "2"
  },
  {
    children: [],
    data: null,
    label: "3",
    value: "3"
  },
  {
    children: [
      {
        children: [],
        data: null,
        label: "4.1",
        value: "4.1"
      },
      {
        children: [],
        data: null,
        label: "4.2",
        value: "4.2"
      }
    ],
    data: null,
    label: "4",
    value: "4"
  }
];

describe("Validate menu data structure", () => {
  it("Properly catches same level duplicated value", () => {
    const menu: IMenu = [
      {
        children: [],
        data: null,
        label: "1",
        value: "1"
      },
      {
        children: [],
        data: null,
        label: "2",
        value: "2"
      },
      {
        children: [],
        data: null,
        label: "1",
        value: "1"
      }
    ];

    expect(validateMenuOptions(menu)).toBeFalsy();
  });

  it("Properly catches multi level duplicated value", () => {
    const menu: IMenu = [
      {
        children: [],
        data: null,
        label: "1",
        value: "1"
      },
      {
        children: [],
        data: null,
        label: "2",
        value: "2"
      },
      {
        children: [],
        data: null,
        label: "3",
        value: "3"
      },
      {
        children: [
          {
            children: [],
            data: null,
            label: "4.1",
            value: "4.1"
          },
          {
            children: [],
            data: null,
            label: "1",
            value: "1"
          }
        ],
        data: null,
        label: "4",
        value: "4"
      }
    ];

    expect(validateMenuOptions(menu)).toBeFalsy();
  });

  it("Properly passes valid structure", () => {
    expect(validateMenuOptions(validMenu)).toBeTruthy();
  });
});

describe("Converting to different representations", () => {
  it("Properly converts to flat structure", () => {
    expect(toFlat(validMenu)).toMatchSnapshot();
  });

  it("Properly converts to nested structure", () => {
    expect(fromFlat(toFlat(validMenu))).toMatchObject(validMenu);
  });
});

describe("Getting items", () => {
  it("Properly returns an item from root by path", () => {
    expect(getMenuItemByPath(validMenu, [1])).toMatchObject(validMenu[1]);
  });

  it("Properly returns an nested item by path", () => {
    expect(getMenuItemByPath(validMenu, [3, 0])).toMatchObject(
      validMenu[3].children[0]
    );
  });

  it("Properly returns an item from root by value", () => {
    expect(getMenuItemByValue(validMenu, validMenu[1].value)).toMatchObject(
      validMenu[1]
    );
  });

  it("Properly returns an nested item by value", () => {
    expect(
      getMenuItemByValue(validMenu, validMenu[3].children[0].value)
    ).toMatchObject(validMenu[3].children[0]);
  });
});

describe("Walk through menu", () => {
  it("Properly returns all nodes on the path", () => {
    expect(walkToMenuItem(validMenu, [3, 0])).toMatchSnapshot();
  });

  it("Properly returns all nodes on the path to root", () => {
    expect(
      walkToRoot(validMenu, validMenu[3].children[0].value)
    ).toMatchSnapshot();
  });
});
