import { storiesOf } from "@storybook/react";
import * as React from "react";

import FileUpload from "@saleor/components/FileUpload";
import Decorator from "../../Decorator";

storiesOf("Components / FileUpload", module)
  .addDecorator(Decorator)
  .add("default", () => <FileUpload />)
  .add("other", () => <FileUpload />);
