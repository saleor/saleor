import * as React from "react";
import { storiesOf } from "@storybook/react";
import {
  Button,
  TextField,
  SelectField,
  Message,
  ProductListItem,
  Form
} from "../../components";

storiesOf("Components", module)
  .add("Button", () => (
    <div className="button-section">
      <Button>Sample Button</Button>
      <Button secondary>Secondary Button</Button>
    </div>
  ))
  .add("Text Field", () => (
    <div className="input-section">
      <TextField label="Input label" defaultValue="Text inside" />
      <TextField
        label="Input label"
        defaultValue="Text inside"
        disabled={true}
      />
      <TextField
        label="Input label"
        defaultValue="Text inside"
        helpText={"Assistive text"}
      />
      <TextField
        label="Input label"
        defaultValue="Text inside"
        errors={[{ message: "There is a problem with this field" }]}
      />
    </div>
  ))
  .add("Select Field", () => (
    <SelectField
      label="Dropdown Label"
      options={[
        { label: "Option I Not available", value: "option1", isDisabled: true },
        { label: "Option II", value: "option2" },
        { label: "Option III", value: "option3" }
      ]}
    />
  ))
  .add("Message", () => (
    <div className="message-section">
      <Message status="success" title="Connection established" visible={true}>
        <p>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque
          eget erat id augue tincidunt aliquam ut efficitur nunc. Nullam in
          venenatis ante. Aenean at felis non sapien interdum.
        </p>
      </Message>
      <Message title="Reconnecting" visible={true}>
        <p>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque
          eget erat id augue tincidunt aliquam ut efficitur nunc. Nullam in
          venenatis ante. Aenean at felis non sapien interdum.
        </p>
      </Message>
      <Message status="error" title="Lost connection" visible={true}>
        <p>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque
          eget erat id augue tincidunt aliquam ut efficitur nunc. Nullam in
          venenatis ante. Aenean at felis non sapien interdum.
        </p>
      </Message>
    </div>
  ))
  .add("Product List Item", () => (
    <div className="product-item-section">
      <ProductListItem
        product={{
          name: "Element T-Shirt Seal Flint Black",
          thumbnail: {
            url: require("../../images/sample-product-thumbnail.png")
          },
          category: {
            name: "T-Shirts"
          },
          price: {
            amount: "50"
          }
        }}
        currency="$"
      />
    </div>
  ))
  .add("Form with validation", () => (
    <Form onSubmit={event => event.preventDefault()}>
      <TextField type="email" label="email" name="email" />
      <TextField type="tel" label="phone" name="phone" required />
      <TextField type="card" label="card" name="card" pattern="[0-9]{13,16}" />
      <TextField
        label="number"
        type="number"
        min="100"
        max="200"
        helpText="Number from 100 to 200"
        name="number"
      />
    </Form>
  ));
