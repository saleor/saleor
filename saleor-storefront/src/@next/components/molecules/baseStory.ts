import { storiesOf } from "@storybook/react";

export const createStory = (name: string = "default") =>
  storiesOf(`@components/molecules/${name}`, module);
