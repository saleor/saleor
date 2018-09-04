import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder255x255.png";
import PointOfInterestField from "../../../components/PointOfInterestField";

storiesOf("components / PointOfInterestField", module).add("default", () => (
  <PointOfInterestField
    src={placeholder}
    onChange={undefined}
    value={"0.5x0.5"}
  />
));
// .add("other", () => <PointOfInterestField />);
