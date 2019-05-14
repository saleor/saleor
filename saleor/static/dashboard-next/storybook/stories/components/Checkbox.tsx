import { storiesOf } from "@storybook/react";
import * as React from "react";

import Checkbox, { CheckboxProps } from "../../../components/Checkbox";
import Form from "../../../components/Form";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: CheckboxProps = {
  checked: false,
  name: "data"
};

storiesOf("Generics / Checkbox", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("checked", () => <Checkbox {...props} checked={true} />)
  .add("unchecked", () => <Checkbox {...props} />)
  .add("undeterminate", () => <Checkbox {...props} indeterminate={true} />)
  .add("interactive", () => (
    <Form initial={{ data: false }}>
      {({ change, data }) => (
        <Checkbox
          {...props}
          checked={data.data}
          // Omit second argument
          onChange={event =>
            change({
              target: {
                name: event.target.name,
                value: !data.data
              }
            } as any)
          }
        />
      )}
    </Form>
  ));
