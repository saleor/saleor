import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeDetailsPage from "../../../attributes/components/AttributeDetailsPage";
import { attributes } from "../../../attributes/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Attributes / Attribute details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <AttributeDetailsPage
      attribute={attributes[0]}
      disabled={false}
      saveButtonBarState="default"
      onBack={() => {}}
      onDelete={() => {}}
      onSubmit={() => {}}
      onValueAdd={() => {}}
      onValueDelete={() => () => {}}
      onValueEdit={() => () => () => {}}
      onValueReorder={() => () => {}}
    />
  ))
  .add("when loading", () => (
    <AttributeDetailsPage
      disabled={true}
      saveButtonBarState="default"
      onBack={() => {}}
      onDelete={() => {}}
      onSubmit={() => {}}
      onValueAdd={() => {}}
      onValueDelete={() => () => {}}
      onValueEdit={() => () => () => {}}
      onValueReorder={() => () => {}}
    />
  ));
