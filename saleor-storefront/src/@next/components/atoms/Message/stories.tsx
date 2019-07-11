import { action } from "@storybook/addon-actions";
import React from "react";

import { Message } from ".";
import { createStory } from "../baseStory";

const onClick = action("onClick called");

const lipsum =
  "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut rutrum arcu lectus, ac viverra sapien volutpat eu. Nam et eros nunc. Nunc rutrum erat eu massa facilisis faucibus. Mauris ultrices eleifend sollicitudin. Vestibulum eleifend cursus arcu, et vehicula turpis blandit a. Fusce vitae arcu bibendum, dapibus felis eu, dignissim orci.";

createStory("Message")
  .add("neutral snackbar", () => (
    <Message title="Sample Message" onClick={onClick} />
  ))
  .add("success w/ children", () => (
    <Message title="Sample Message" status="success" onClick={onClick}>
      {lipsum}
    </Message>
  ))
  .add("error w/ children", () => (
    <Message title="Sample Message" status="error" onClick={onClick}>
      {lipsum}
    </Message>
  ))
  .add("action snackbar", () => (
    <Message
      title="Sample Message"
      status="action"
      onClick={onClick}
      actionText="Try again"
    />
  ))
  .add("action card", () => (
    <Message
      title="Sample Message"
      status="action"
      onClick={onClick}
      actionText="Refresh"
    >
      {lipsum}
    </Message>
  ));
