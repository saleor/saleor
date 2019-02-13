import { storiesOf } from "@storybook/react";
import * as React from "react";

import Form from "../../../components/Form";
import RichTextEditor from "../../../components/RichTextEditor";
import Decorator from "../../Decorator";

storiesOf("Generics / Rich text editor", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Form
      initial={{
        content: null
      }}
    >
      {({ change, data }) => (
        <RichTextEditor
          disabled={false}
          initial={data.content}
          label="Content"
          name="content"
          onChange={change}
        />
      )}
    </Form>
  ));
