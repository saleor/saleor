import * as React from "react";
import * as renderer from "react-test-renderer";

import { TimezoneProvider } from "../Timezone";
import Date from "./Date";

const expected = "Apr 7, 2018";

test("Render with timezone GMT-11", () => {
  const date = renderer.create(
    <TimezoneProvider value="Pacific/Midway">
      <Date date="2018-04-07" plain />
    </TimezoneProvider>
  );
  expect(date.toJSON()).toEqual(expected);
});

test("Render with timezone GMT+13", () => {
  const date = renderer.create(
    <TimezoneProvider value="Pacific/Tongatapu">
      <Date date="2018-04-07" plain />
    </TimezoneProvider>
  );
  expect(date.toJSON()).toEqual(expected);
});
