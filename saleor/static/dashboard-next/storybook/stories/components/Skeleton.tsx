import { storiesOf } from "@storybook/react";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";

storiesOf("Generics / Skeleton", module).add("default", () => (
  <Skeleton style={{ maxWidth: 300 }} />
));
