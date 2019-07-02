import React from "react";
import renderer from "react-test-renderer";

import { TimezoneProvider } from "../Timezone";
import Date from "./Date";

const testDate = "2018-04-07";
const expectedDate = "Apr 7, 2018";

test("Render plain date with timezone GMT-11", () => {
  const date = renderer.create(
    <TimezoneProvider value="Pacific/Midway">
      <Date date={testDate} plain />
    </TimezoneProvider>
  );
  expect(date.toJSON()).toEqual(expectedDate);
});

test("Render plain date with timezone GMT+13", () => {
  const date = renderer.create(
    <TimezoneProvider value="Pacific/Tongatapu">
      <Date date={testDate} plain />
    </TimezoneProvider>
  );
  expect(date.toJSON()).toEqual(expectedDate);
});

test("Render humanized date with timezone GMT-11", () => {
  const date = renderer.create(
    <TimezoneProvider value="Pacific/Midway">
      <Date date={testDate} />
    </TimezoneProvider>
  );
  expect(date.toJSON().props.dateTime).toEqual(testDate);
});

test("Render humanized date with timezone GMT+13", () => {
  const date = renderer.create(
    <TimezoneProvider value="Pacific/Tongatapu">
      <Date date={testDate} />
    </TimezoneProvider>
  );
  expect(date.toJSON().props.dateTime).toEqual(testDate);
});
