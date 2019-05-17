import { SelectMenuItem, validateOptions } from "./AutocompleteSelectMenu";

describe("Validate Autocomplete Menu data structure", () => {
  it("Properly catches same level duplicated value", () => {
    const menu: SelectMenuItem[] = [
      {
        label: "1",
        value: "1"
      },
      {
        label: "2",
        value: "2"
      },
      {
        label: "1",
        value: "1"
      }
    ];

    expect(validateOptions(menu)).toBeFalsy();
  });

  it("Properly catches multi level duplicated value", () => {
    const menu: SelectMenuItem[] = [
      {
        label: "1",
        value: "1"
      },
      {
        label: "2",
        value: "2"
      },
      {
        label: "3",
        value: "3"
      },
      {
        children: [
          {
            label: "4.1",
            value: "4.1"
          },
          {
            label: "1",
            value: "1"
          }
        ],
        label: "4"
      }
    ];

    expect(validateOptions(menu)).toBeFalsy();
  });

  it("Properly passes valid structure", () => {
    const menu: SelectMenuItem[] = [
      {
        label: "1",
        value: "1"
      },
      {
        label: "2",
        value: "2"
      },
      {
        label: "3",
        value: "3"
      },
      {
        children: [
          {
            label: "4.1",
            value: "4.1"
          },
          {
            label: "4.2",
            value: "4.2"
          }
        ],
        label: "4"
      }
    ];

    expect(validateOptions(menu)).toBeTruthy();
  });
});
