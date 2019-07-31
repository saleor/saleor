import {
  add,
  addAtIndex,
  isSelected,
  move,
  remove,
  removeAtIndex,
  toggle,
  updateAtIndex
} from "./lists";

const initialArray = ["lorem", "ipsum", "dolor"];

describe("Properly calculates output arrays", () => {
  it("Adds", () => {
    expect(add("sit", initialArray)).toMatchSnapshot();
  });

  it("Adds at index", () => {
    expect(addAtIndex("sit", initialArray, 2)).toMatchSnapshot();
  });

  it("Updates at index", () => {
    expect(updateAtIndex("amet", initialArray, 1)).toMatchSnapshot();
  });

  it("Removes", () => {
    expect(remove("ipsum", initialArray, (a, b) => a === b)).toMatchSnapshot();
  });

  it("Removes at index", () => {
    expect(removeAtIndex(initialArray, 1)).toMatchSnapshot();
  });

  it("Matches", () => {
    expect(isSelected("lorem", initialArray, (a, b) => a === b)).toBe(true);
    expect(isSelected("sit", initialArray, (a, b) => a === b)).toBe(false);
  });

  it("Toggles", () => {
    expect(toggle("lorem", initialArray, (a, b) => a === b)).toMatchSnapshot();
    expect(toggle("sit", initialArray, (a, b) => a === b)).toMatchSnapshot();
  });

  it("Moves", () => {
    expect(move("lorem", initialArray, (a, b) => a === b, 1)).toMatchSnapshot();
  });
});
