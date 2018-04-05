import { storiesOf } from "@storybook/react";
import * as React from "react";

import ErrorMessageCard from "../../../components/ErrorMessageCard";

storiesOf("Generics / ErrorMessageCard", module).add("default", () => (
  <ErrorMessageCard message="Loren ipsum dolor sit amet!" />
));
